"""Асинхронный модуль с обработчиком клиентских запросов"""

import asyncio
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
    Асинхронный обработчик запросов от одного клиента
    """

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, logger: Logger
    ) -> None:
        """
        Инициализация асинхронного обработчика запросов

        Args:
            reader: StreamReader для чтения данных от клиента
            writer: StreamWriter для отправки данных клиенту
            logger: Объект для логирования
        """
        self.reader = reader
        self.writer = writer
        self.logger = logger
        self.client_ip: str = writer.get_extra_info("peername")[0]

        self.http_client: HttpClient = HttpClient()
        self.conn_manager: ConnectionManager = ConnectionManager()
        self.dns_resolver: DnsResolver = DnsResolver()

    async def run(self) -> None:
        """
        Главный асинхронный метод обработки запроса
        """
        start_time = time.time()

        try:
            request_data = await self._read_request()
            if not request_data:
                raise BadRequestException("Пустой запрос")

            request_line = request_data.split("\r\n")[0]
            self.logger.log(f"[{self.client_ip}] Запрос: {request_line}")

            method = request_line.split(" ")[0]

            if method == "CONNECT":
                await self._handle_https(request_data)
            else:
                await self._handle_http(request_data)

            processing_time = int((time.time() - start_time) * 1000)
            self.logger.log(
                f"[{self.client_ip}] Обработка завершена за {processing_time} мс"
            )

        except BadRequestException as e:
            await self._send_error_response(e.error_code, e.message)
            self.logger.log(f"[{self.client_ip}] {e.error_code}: {e.message}")
        except ConnectionRefusedException as e:
            await self._send_error_response(e.error_code, e.message)
            self.logger.log(f"[{self.client_ip}] {e.error_code}: {e.message}")
        except Exception as e:
            await self._send_error_response(500, f"Internal Server Error: {str(e)}")
            self.logger.log(f"[{self.client_ip}] 500: {str(e)}")
        finally:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

    async def _read_request(self) -> Optional[str]:
        """Асинхронно читает сырой запрос от клиента"""
        try:
            data = await asyncio.wait_for(self.reader.read(65535), timeout=30)
            return data.decode("utf-8", errors="replace")
        except Exception:
            return None

    async def _handle_http(self, request_data: str) -> None:
        """Асинхронно обрабатывает HTTP запрос (GET, POST, PUT, DELETE...)"""
        lines = request_data.split("\r\n")
        if not lines:
            raise BadRequestException("Некорректный запрос")

        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) < 3:
            raise BadRequestException("Некорректная строка запроса")

        method = parts[0]
        full_url = parts[1]
        http_version = parts[2]
        headers = self._parse_headers(lines[1:])

        host, port = self._extract_host_port(full_url, headers)
        path = self._extract_path(full_url)

        ip = await self.dns_resolver.resolve(host)
        self.logger.log(f"[{self.client_ip}] DNS: {host} -> {ip}")

        conn_info = self.conn_manager.get_connection(host, port)
        is_new = conn_info is None

        if is_new:
            server_reader, server_writer = await self.conn_manager.open_connection(
                ip, port
            )
            self.logger.log(f"[{self.client_ip}] Новое соединение с {host}:{port}")
        else:
            server_reader, server_writer = conn_info
            self.logger.log(
                f"[{self.client_ip}] Переиспользовано соединение с {host}:{port}"
            )

        request_to_server = f"{method} {path} {http_version}\r\n"
        request_to_server += f"Host: {host}\r\n"
        for header, value in headers.items():
            if header.lower() != "host":
                request_to_server += f"{header}: {value}\r\n"
        request_to_server += "\r\n"

        transfer_start = time.time()
        response = await self.http_client.send_and_receive(
            server_reader, server_writer, request_to_server
        )
        transfer_time = int((time.time() - transfer_start) * 1000)

        self.writer.write(response.encode("utf-8"))
        await self.writer.drain()

        status_code = self._extract_status_code(response)
        bytes_transferred = len(response.encode("utf-8"))
        url_to_log = host + path
        self.logger.log_request(
            self.client_ip,
            method,
            url_to_log,
            status_code,
            bytes_transferred,
            transfer_time,
        )

        keep_alive = (
            "Connection: keep-alive" in request_to_server.lower()
            or "Connection: keep-alive" in response.lower()
        )

        if keep_alive and self.conn_manager.keep_alive:
            self.conn_manager.save_connection(host, port, server_reader, server_writer)
            self.logger.log(f"[{self.client_ip}] Соединение сохранено (Keep-Alive)")
        else:
            self.conn_manager.close_connection(host, port)
            self.logger.log(f"[{self.client_ip}] Соединение закрыто")

    async def _handle_https(self, request_data: str) -> None:
        """Асинхронно обрабатывает HTTPS CONNECT запрос"""
        request_line = request_data.split("\r\n")[0]
        parts = request_line.split(" ")
        if len(parts) < 2:
            raise BadRequestException("Некорректный CONNECT запрос")

        host_port = parts[1]
        if ":" not in host_port:
            raise BadRequestException("Некорректный CONNECT запрос: нет порта")

        host, port_str = host_port.split(":")
        port = int(port_str)

        self.logger.log(f"[{self.client_ip}] HTTPS CONNECT к {host}:{port}")

        try:
            server_reader, server_writer = await asyncio.open_connection(host, port)
            self.logger.log(
                f"[{self.client_ip}] Соединение с {host}:{port} установлено"
            )
        except Exception:
            raise ConnectionRefusedException(host, port)

        response = "HTTP/1.1 200 Connection established\r\n"
        response += "Proxy-agent: PythonWebProxy/1.0\r\n"
        response += "\r\n"
        self.writer.write(response.encode("utf-8"))
        await self.writer.drain()

        self.logger.log(f"[{self.client_ip}] Туннель для {host}:{port} установлен")

        await self._relay_data(self.reader, self.writer, server_reader, server_writer)

        self.logger.log(f"[{self.client_ip}] Туннель для {host}:{port} закрыт")

    async def _relay_data(
        self,
        client_r: asyncio.StreamReader,
        client_w: asyncio.StreamWriter,
        server_r: asyncio.StreamReader,
        server_w: asyncio.StreamWriter,
    ) -> None:
        """
        Асинхронно создаёт двусторонний туннель между клиентом и сервером
        """

        async def forward(
            src_r: asyncio.StreamReader, dst_w: asyncio.StreamWriter
        ) -> None:
            try:
                while True:
                    data = await src_r.read(8192)
                    if not data:
                        break
                    dst_w.write(data)
                    await dst_w.drain()
            except Exception:
                pass

        task1 = asyncio.create_task(forward(client_r, server_w))
        task2 = asyncio.create_task(forward(server_r, client_w))

        await asyncio.gather(task1, task2)

    def _parse_headers(self, lines: list) -> dict:
        """Парсит заголовки HTTP запроса"""
        headers = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return headers

    def _extract_host_port(self, full_url: str, headers: dict) -> Tuple[str, int]:
        """Извлекает хост и порт из URL или заголовка Host"""
        if full_url.startswith("http://"):
            without_http = full_url[7:]
            if "/" in without_http:
                host_part = without_http.split("/")[0]
            else:
                host_part = without_http

            if ":" in host_part:
                host, port_str = host_part.split(":")
                return host, int(port_str)
            return host_part, 80

        if "Host" in headers:
            host_header = headers["Host"]
            if ":" in host_header:
                host, port_str = host_header.split(":")
                return host, int(port_str)
            return host_header, 80

        raise BadRequestException("Не удалось определить хост")

    def _extract_path(self, full_url: str) -> str:
        """Извлекает путь из URL"""
        if full_url.startswith("http://"):
            after_http = full_url[7:]
            if "/" in after_http:
                return "/" + after_http.split("/", 1)[1]
            return "/"
        return full_url

    def _extract_status_code(self, response: str) -> int:
        """Извлекает HTTP статус код из ответа сервера"""
        match = re.search(r"HTTP/\d\.\d (\d+)", response)
        if match:
            return int(match.group(1))
        return 0

    def _build_error_response_string(self, code: int, message: str) -> str:
        """Создаёт HTML страницу с ошибкой (синхронный метод для тестирования)"""
        return f"""HTTP/1.1 {code} {message}
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
</html>"""

    async def _send_error_response(self, code: int, message: str) -> None:
        """Отправляет клиенту HTML страницу с ошибкой"""
        try:
            response = self._build_error_response_string(code, message)
            self.writer.write(response.encode("utf-8"))
            await self.writer.drain()
        except Exception:
            pass

        def _build_http_request_string(
            self, method: str, path: str, http_version: str, host: str, headers: dict
        ) -> str:
            """Создаёт строку HTTP запроса (синхронный метод)"""
            request = f"{method} {path} {http_version}\r\n"
            request += f"Host: {host}\r\n"
            for header, value in headers.items():
                if header.lower() != "host":
                    request += f"{header}: {value}\r\n"
            request += "\r\n"
            return request

        def _should_keep_alive(self, request: str, response: str) -> bool:
            """Определяет нужно ли сохранять соединение (синхронный метод)"""
            return (
                "Connection: keep-alive" in request.lower()
                or "Connection: keep-alive" in response.lower()
            )
