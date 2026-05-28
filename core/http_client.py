"""Асинхронный модуль для отправки HTTP-запросов и получения ответов"""

import asyncio
from exceptions import TimeoutException


class HttpClient:
    """
    Асинхронный HTTP клиент для отправки запросов и получения ответов
    """

    TIMEOUT_MS: int = 30000
    BUFFER_SIZE: int = 8192

    async def send_and_receive(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, request: str
    ) -> str:
        """
        Асинхронно отправляет запрос через переданный сокет и возвращает ответ

        Args:
            reader: StreamReader для чтения ответа
            writer: StreamWriter для отправки запроса
            request: Текст HTTP запроса

        Returns:
            Текст HTTP ответа от сервера

        Raises:
            TimeoutException: Если сервер не отвечает в течение TIMEOUT_MS
        """
        try:
            writer.write(request.encode("utf-8"))
            await writer.drain()

            response = bytearray()
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        reader.read(self.BUFFER_SIZE), self.TIMEOUT_MS / 1000
                    )
                    if not chunk:
                        break
                    response.extend(chunk)
                    if b"\r\n\r\n" in response:
                        # Получили заголовки, можно прекратить чтение
                        break
                except asyncio.TimeoutError:
                    break

            return response.decode("utf-8", errors="replace")

        except asyncio.TimeoutError:
            raise TimeoutException(self.TIMEOUT_MS)
