"""Модуль с классами исключений для прокси-сервера"""


class ProxyError(Exception):
    """Базовый класс для всех ошибок прокси"""

    def __init__(self, error_code: int, message: str) -> None:
        """
        Инициализация ошибки прокси

        Args:
            error_code: HTTP код ошибки (400, 502, 504 и т.д.)
            message: Текстовое описание ошибки
        """
        self.error_code: int = error_code
        self.message: str = message
        super().__init__(message)

    def get_error_code(self) -> int:
        """Возвращает HTTP код ошибки"""
        return self.error_code


class BadRequestException(ProxyError):
    """Ошибка 400 - некорректный запрос клиента"""

    def __init__(self, message: str) -> None:
        """Инициализация ошибки 400 Bad Request"""
        super().__init__(400, message)


class ConnectionRefusedException(ProxyError):
    """Ошибка 502 - не удалось соединиться с целевым сервером"""

    def __init__(self, host: str, port: int) -> None:
        """Инициализация ошибки 502 Bad Gateway"""
        super().__init__(502, f"Не удалось соединиться с {host}:{port}")


class TimeoutException(ProxyError):
    """Ошибка 504 - превышен таймаут ожидания ответа от сервера"""

    def __init__(self, timeout_ms: int) -> None:
        """Инициализация ошибки 504 Gateway Timeout"""
        super().__init__(504, f"Превышен таймаут: {timeout_ms} мс")