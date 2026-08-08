"""Асинхронный модуль для DNS резолвинга
(преобразование доменов в IP-адреса)"""

import asyncio
from threading import Lock
from exceptions import BadRequestException


class DnsResolver:
    """
    Асинхронный DNS резолвер с кэшированием
    """

    def __init__(self) -> None:
        """Инициализация DNS резолвера с пустым кэшем"""
        self._cache: dict = {}
        self._lock: Lock = Lock()

    async def resolve(self, hostname: str) -> str:
        """
        Асинхронно преобразует доменное имя в IP-адрес

        Args:
            hostname: Доменное имя (например, "google.com")

        Returns:
            IP-адрес в виде строки (например, "142.250.185.46")

        Raises:
            BadRequestException: Если домен не удалось разрешить
        """
        with self._lock:
            if hostname in self._cache:
                return self._cache[hostname]

        try:
            loop = asyncio.get_event_loop()
            ip = await loop.getaddrinfo(hostname,
                                        80, family=1, type=1, proto=6)
            result: str = ip[0][4][0]
            with self._lock:
                self._cache[hostname] = result
            return result
        except Exception as e:
            raise BadRequestException(
                f"Не удалось разрешить домен: {hostname} - {e}")
