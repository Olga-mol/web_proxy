"""Модуль для логирования работы прокси-сервера"""

import logging
from pathlib import Path


class Logger:
    """Класс для записи логов в файл и консоль"""

    def __init__(self, log_file: str = "proxy.log") -> None:
        """
        Инициализация логгера

        Args:
            log_file: Путь к файлу для
            сохранения логов (по умолчанию proxy.log)
        """
        self.log_file: Path = Path(log_file)

        self.logger = logging.getLogger("WebProxy")
        self.logger.setLevel(logging.INFO)

        self.logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, message: str) -> None:
        """
        Записывает обычное сообщение в лог

        Args:
            message: Текст сообщения для записи
        """
        self.logger.info(message)

    def log_request(
        self,
        client_ip: str,
        method: str,
        url: str,
        status_code: int,
        bytes_transferred: int,
        processing_time_ms: int,
    ) -> None:
        """
        Записывает информацию об HTTP запросе в специальном формате

        Формат: "IP | МЕТОД | URL | КОД | БАЙТ | ВРЕМЯ"

        Args:
            client_ip: IP-адрес клиента
            method: HTTP метод (GET, POST, CONNECT...)
            url: Запрашиваемый URL
            status_code: HTTP статус код ответа
            bytes_transferred: Количество переданных байт
            processing_time_ms: Время обработки запроса в миллисекундах
        """
        self.log(
            f"{client_ip} | {method} | {url} | {status_code} "
            f"| {bytes_transferred} байт | {processing_time_ms} мс"
        )

    def close(self) -> None:
        """Закрывает логгер и освобождает ресурсы"""
        logging.shutdown()
