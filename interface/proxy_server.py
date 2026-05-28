"""Асинхронный модуль с главным сервером прокси"""

import asyncio
import sys
from typing import Optional

from .logger import Logger


class ProxyServer:
    """
    Асинхронный главный сервер прокси
    """

    def __init__(self, port: int = 8080, max_workers: int = 100) -> None:
        """
        Инициализация асинхронного прокси-сервера

        Args:
            port: Номер порта для прослушивания (по умолчанию 8080)
            max_workers: Максимальное количество одновременных задач
        """
        self.port: int = port
        self.max_workers: int = max_workers
        self.logger: Logger = Logger()
        self.server: Optional[asyncio.Server] = None
        self.running: bool = False

    async def start(self) -> None:
        """
        Асинхронно запускает прокси-сервер
        """
        try:
            self.server = await asyncio.start_server(
                self._handle_client, "0.0.0.0", self.port, limit=65535
            )
            self.running = True

            self.logger.log(f"Прокси-сервер запущен на порту {self.port}")
            self.logger.log(f"Настройте браузер на localhost:{self.port}")

            async with self.server:
                await self.server.serve_forever()

        except asyncio.CancelledError:
            self.logger.log("Сервер остановлен")
            sys.exit(0)
        except OSError as e:
            self.logger.log(
                f"Ошибка: не удалось запустить сервер на порту {self.port} - {e}"
            )
            sys.exit(1)
        except Exception as e:
            self.logger.log(f"Критическая ошибка сервера: {e}")
            sys.exit(4)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Обрабатывает подключение нового клиента

        Args:
            reader: StreamReader для чтения данных от клиента
            writer: StreamWriter для отправки данных клиенту
        """
        # Импорт ВНУТРИ метода для избежания циклического импорта
        from core.request_handler import RequestHandler

        client_ip = writer.get_extra_info("peername")[0]
        self.logger.log(f"Новое подключение от {client_ip}")

        handler = RequestHandler(reader, writer, self.logger)
        await handler.run()

    def stop(self) -> None:
        """Останавливает прокси-сервер"""
        self.running = False
        if self.server:
            self.server.close()
        self.logger.log("Прокси-сервер остановлен")
        self.logger.close()
