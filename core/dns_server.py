"""Модуль для DNS резолвинга (преобразование доменов в IP-адреса)"""

import socket
from threading import Lock
from exceptions import BadRequestException


class DnsResolver:
    """
    Преобразует доменные имена в IP-адреса с кэшированием

    Пример: google.com → 142.250.185.46
    """

    def __init__(self) -> None:
        """Инициализация DNS резолвера с пустым кэшем"""
        self._cache: dict = {}
        self._lock: Lock = Lock()

    def resolve(self, hostname: str) -> str:
        """
        Преобразует доменное имя в IP-адрес
        Сначала проверяет кэш, если нет — выполняет DNS запрос
        Результат сохраняется в кэш для ускорения следующих запросов

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
            ip: str = socket.gethostbyname(hostname)
            with self._lock:
                self._cache[hostname] = ip
            return ip
        except socket.gaierror:
            raise BadRequestException(f"Не удалось разрешить домен: {hostname}")