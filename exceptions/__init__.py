"""Пакет исключений прокси-сервера"""

from .proxy_errors import (
    ProxyError,
    BadRequestException,
    ConnectionRefusedException,
    TimeoutException,
)

__all__ = [
    "ProxyError",
    "BadRequestException",
    "ConnectionRefusedException",
    "TimeoutException",
]
