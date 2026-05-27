"""Модуль для отправки HTTP-запросов и получения ответов"""

import socket
from exceptions import TimeoutException


class HttpClient:
    """
    Отправляет запросы на сервер и получает ответы

    Умеет обрабатывать таймауты и читать данные порциями
    """

    TIMEOUT_MS: int = 30000  # 30 секунд
    BUFFER_SIZE: int = 8192  # 8KB

    def send_and_receive(self, sock: socket.socket, request: str) -> str:
        """
        Отправляет запрос через переданный сокет и возвращает ответ

        Args:
            sock: Сокет для отправки запроса
            request: Текст HTTP запроса

        Returns:
            Текст HTTP ответа от сервера

        Raises:
            TimeoutException: Если сервер не отвечает в течение TIMEOUT_MS
        """
        sock.settimeout(self.TIMEOUT_MS / 1000)

        try:
            sock.send(request.encode('utf-8'))

            response = bytearray()
            sock.settimeout(self.TIMEOUT_MS / 1000)

            while True:
                try:
                    chunk = sock.recv(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    response.extend(chunk)
                    if b'\r\n\r\n' in response:
                        sock.settimeout(0.5)
                except socket.timeout:
                    break

            return response.decode('utf-8', errors='replace')

        except socket.timeout:
            raise TimeoutException(self.TIMEOUT_MS)