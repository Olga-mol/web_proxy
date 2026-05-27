"""Модуль с обработчиком клиентских запросов"""

import socket
import threading
import re
import time
from typing import Optional, Tuple

from interface.logger import Logger
from .dns_server import DnsResolver
from .connection_manager import ConnectionManager
from .http_client import HttpClient
from exceptions import BadRequestException, ConnectionRefusedException


class RequestHandler:
    """
    Обрабатывает запросы от одного клиента

    Это главный класс-дирижёр, который:
    - Определяет тип запроса (HTTP или HTTPS)
    - Координирует работу DNS, ConnectionManager и HttpClient
    - Формирует ответ клиенту
    """

    def __init__(self, client_socket: socket.socket, logger: Logger) -> None:
        """
        Инициализация обработчика запросов

        Args:
            client_socket: Сокет для общения с клиентом
            logger: Объект для логирования
        """
        self.client_socket: socket.socket = client_socket
        self.logger: Logger = logger
        self.client_ip: str = client_socket.getpeername()[0]

        self.http_client: HttpClient = HttpClient()
        self.conn_manager: ConnectionManager = ConnectionManager()
        self.dns_resolver: DnsResolver = DnsResolver()

    def run(self) -> None:
        """
        Главный метод обработки запроса

        Читает запрос от клиента, определяет метод (CONNECT или другой),
        вызывает соответствующий обработчик и логирует время выполнения
        """
        start_time = time.time()

        try:
            request_data = self._read_request()
            if not request_data:
                raise BadRequestException("Пустой запрос")

            request_line = request_data.split('\r\n')[0]
            self.logger.log(f"[{self.client_ip}] Запрос: {request_line}")

            method = request_line.split(' ')[0]

            if method == "CONNECT":
                self._handle_https(request_data)
            else:
                self._handle_http(request_data)

            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log(f"[{self.client_ip}] Обработка завершена за {processing_time} мс")

        except BadRequestException as e:
            self._send_error_response(e.error_code, e.message)
            self.logger.log(f"[{self.client_ip}] {e.error_code}: {e.message}")
        except ConnectionRefusedException as e:
            self._send_error_response(e.error_code, e.message)
            self.logger.log(f"[{self.client_ip}] {e.error_code}: {e.message}")
        except Exception as e:
            self._send_error_response(500, f"Internal Server Error: {str(e)}")
            self.logger.log(f"[{self.client_ip}] 500: {str(e)}")
        finally:
            try:
                self.client_socket.close()
            except Exception:
                pass

    def _read_request(self) -> Optional[str]:
        """
        Читает сырой запрос от клиента

        Returns:
            Текст запроса или None при ошибке
        """
        try:
            data = self.client_socket.recv(65535)
            return data.decode('utf-8', errors='replace')
        except Exception:
            return None

    def _handle_http(self, request_data: str) -> None:
        """
        Обрабатывает HTTP запрос (GET, POST, PUT, DELETE...)

        Алгоритм:
        1. Парсит запрос, извлекает хост, порт, путь
        2. Выполняет DNS резолвинг
        3. Получает или создаёт соединение с сервером
        4. Отправляет запрос и получает ответ
        5. Пересылает ответ клиенту
        6. Решает, сохранять соединение для Keep-Alive или закрыть

        Args:
            request_data: Сырой текст HTTP запроса от клиента
        """
        lines = request_data.split('\r\n')
        if not lines:
            raise BadRequestException("Некорректный запрос")

        request_line = lines[0]
        parts = request_line.split(' ')
        if len(parts) < 3:
            raise BadRequestException("Некорректная строка запроса")

        method = parts[0]
        full_url = parts[1]
        http_version = parts[2]
        headers = self._parse_headers(lines[1:])

        host, port = self._extract_host_port(full_url, headers)
        path = self._extract_path(full_url)

        ip = self.dns_resolver.resolve(host)
        self.logger.log(f"[{self.client_ip}] DNS: {host} -> {ip}")

        server_socket = self.conn_manager.get_connection(host, port)
        is_new = server_socket is None

        if is_new:
            server_socket = self.conn_manager.open_connection(ip, port)
            self.logger.log(f"[{self.client_ip}] Новое соединение с {host}:{port}")
        else:
            self.logger.log(f"[{self.client_ip}] Переиспользовано соединение с {host}:{port}")

        request_to_server = f"{method} {path} {http_version}\r\n"
        request_to_server += f"Host: {host}\r\n"
        for header, value in headers.items():
            if header.lower() != 'host':
                request_to_server += f"{header}: {value}\r\n"
        request_to_server += "\r\n"

        transfer_start = time.time()
        response = self.http_client.send_and_receive(server_socket, request_to_server)
        transfer_time = int((time.time() - transfer_start) * 1000)

        self.client_socket.send(response.encode('utf-8'))

        status_code = self._extract_status_code(response)
        bytes_transferred = len(response.encode('utf-8'))
        url_to_log = host + path
        self.logger.log_request(self.client_ip, method, url_to_log,
                                status_code, bytes_transferred, transfer_time)

        keep_alive = 'Connection: keep-alive' in request_to_server.lower() or \
                     'Connection: keep-alive' in response.lower()

        if keep_alive and self.conn_manager.keep_alive:
            self.conn_manager.save_connection(host, port, server_socket)
            self.logger.log(f"[{self.client_ip}] Соединение сохранено (Keep-Alive)")
        else:
            self.conn_manager.close_connection(server_socket)
            self.logger.log(f"[{self.client_ip}] Соединение закрыто")

    def _handle_https(self, request_data: str) -> None:
        """
        Обрабатывает HTTPS CONNECT запрос

        Для HTTPS создаётся туннель:
        1. Соединяется с целевым сервером
        2. Отправляет клиенту "200 Connection established"
        3. Запускает двустороннюю пересылку данных (туннель)

        Args:
            request_data: Сырой текст CONNECT запроса от клиента
        """
        request_line = request_data.split('\r\n')[0]
        parts = request_line.split(' ')
        if len(parts) < 2:
            raise BadRequestException("Некорректный CONNECT запрос")

        host_port = parts[1]
        if ':' not in host_port:
            raise BadRequestException("Некорректный CONNECT запрос: нет порта")

        host, port_str = host_port.split(':')
        port = int(port_str)

        self.logger.log(f"[{self.client_ip}] HTTPS CONNECT к {host}:{port}")

        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(30)
            server_socket.connect((host, port))
            self.logger.log(f"[{self.client_ip}] Соединение с {host}:{port} установлено")
        except Exception:
            raise ConnectionRefusedException(host, port)

        response = "HTTP/1.1 200 Connection established\r\n"
        response += "Proxy-agent: PythonWebProxy/1.0\r\n"
        response += "\r\n"
        self.client_socket.send(response.encode('utf-8'))

        self.logger.log(f"[{self.client_ip}] Туннель для {host}:{port} установлен")

        self._relay_data(self.client_socket, server_socket)

        self.logger.log(f"[{self.client_ip}] Туннель для {host}:{port} закрыт")

    def _forward(self, src: socket.socket, dst: socket.socket) -> None:
        """
        Пересылает данные из одного сокета в другой

        Используется внутри _relay_data для двусторонней пересылки

        Args:
            src: Сокет-источник (откуда читаем)
            dst: Сокет-назначение (куда пишем)
        """
        try:
            while True:
                data = src.recv(8192)
                if not data:
                    break
                dst.send(data)
        except Exception:
            pass

    def _relay_data(self, client_sock: socket.socket, server_sock: socket.socket) -> None:
        """
        Создаёт двусторонний туннель между клиентом и сервером

        Запускает два потока:
        - Один передаёт данные клиент → сервер
        - Второй передаёт данные сервер → клиент

        Args:
            client_sock: Сокет клиента
            server_sock: Сокет сервера
        """
        t1 = threading.Thread(target=self._forward, args=(client_sock, server_sock))
        t2 = threading.Thread(target=self._forward, args=(server_sock, client_sock))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

        t1.join()
        t2.join()

    def _parse_headers(self, lines: list) -> dict:
        """
        Парсит заголовки HTTP запроса

        Args:
            lines: Список строк заголовков

        Returns:
            Словарь вида {название_заголовка: значение}
        """
        headers = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        return headers

    def _extract_host_port(self, full_url: str, headers: dict) -> Tuple[str, int]:
        """
        Извлекает хост и порт из URL или заголовка Host

        Args:
            full_url: Полный URL запроса
            headers: Словарь заголовков

        Returns:
            Кортеж (хост, порт)

        Raises:
            BadRequestException: Если не удалось определить хост
        """
        if full_url.startswith('http://'):
            without_http = full_url[7:]
            if '/' in without_http:
                host_part = without_http.split('/')[0]
            else:
                host_part = without_http

            if ':' in host_part:
                host, port_str = host_part.split(':')
                return host, int(port_str)
            return host_part, 80

        if 'Host' in headers:
            host_header = headers['Host']
            if ':' in host_header:
                host, port_str = host_header.split(':')
                return host, int(port_str)
            return host_header, 80

        raise BadRequestException("Не удалось определить хост")

    def _extract_path(self, full_url: str) -> str:
        """
        Извлекает путь из URL

        Args:
            full_url: Полный URL запроса

        Returns:
            Путь (например, "/index.html")
        """
        if full_url.startswith('http://'):
            after_http = full_url[7:]
            if '/' in after_http:
                return '/' + after_http.split('/', 1)[1]
            return '/'
        return full_url

    def _extract_status_code(self, response: str) -> int:
        """
        Извлекает HTTP статус код из ответа сервера

        Args:
            response: Текст HTTP ответа

        Returns:
            HTTP статус код (200, 404, 500...) или 0, если не найден
        """
        match = re.search(r'HTTP/\d\.\d (\d+)', response)
        if match:
            return int(match.group(1))
        return 0

    def _send_error_response(self, code: int, message: str) -> None:
        """
        Отправляет клиенту HTML страницу с ошибкой

        Args:
            code: HTTP код ошибки
            message: Текстовое описание ошибки
        """
        try:
            response = f"""HTTP/1.1 {code} {message}
Content-Type: text/html; charset=utf-8
Connection: close

<!DOCTYPE html>
<html>
<head><title>{code} {message}</title></head>
<body>
<h1>{code} {message}</h1>
<hr>
<p>Simple Python Web Proxy</p>
</body>
</html>
"""
            self.client_socket.send(response.encode('utf-8'))
        except Exception:
            pass