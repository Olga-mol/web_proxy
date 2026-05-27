"""Модуль с главным сервером прокси"""

import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from .logger import Logger
from core.request_handler import RequestHandler


class ProxyServer:
    """
    Главный сервер прокси

    Отвечает за:
    - Запуск TCP сервера на указанном порту
    - Приём входящих подключений
    - Создание обработчиков для каждого клиента
    """

    def __init__(self, port: int = 8080, max_workers: int = 100) -> None:
        """
        Инициализация прокси-сервера

        Args:
            port: Номер порта для прослушивания (по умолчанию 8080)
            max_workers: Максимальное количество одновременных потоков
        """
        self.port: int = port
        self.max_workers: int = max_workers
        self.logger: Logger = Logger()
        self.server_socket: Optional[socket.socket] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.running: bool = False

    def start(self) -> None:
        """
        Запускает прокси-сервер

        Создаёт сокет, начинает слушать порт и принимает подключения
        Для каждого клиента создаётся отдельный RequestHandler в новом потоке
        Работает в бесконечном цикле до вызова stop() или нажатия Ctrl+C
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(100)

            self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
            self.running = True

            self.logger.log(f"Прокси-сервер запущен на порту {self.port}")
            self.logger.log(f"Настройте браузер на localhost:{self.port}")

            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    client_ip = client_addr[0]
                    self.logger.log(f"Новое подключение от {client_ip}")

                    handler = RequestHandler(client_socket, self.logger)
                    self.thread_pool.submit(handler.run)

                except OSError:
                    if self.running:
                        self.logger.log("Ошибка сокета")
                    break

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.log(f"Критическая ошибка сервера: {e}")

    def stop(self) -> None:
        """
        Останавливает прокси-сервер

        Закрывает серверный сокет, завершает все потоки в пуле
        и закрывает логгер
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        self.logger.log("Прокси-сервер остановлен")
        self.logger.close()