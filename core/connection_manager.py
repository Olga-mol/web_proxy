"""Асинхронный модуль для управления соединениями (Keep-Alive)"""

import asyncio
from typing import Optional, Dict, Tuple


class ConnectionManager:
    """
    Асинхронный менеджер для управления пулом постоянных соединений
    """

    def __init__(self) -> None:
        """Инициализация асинхронного менеджера соединений"""
        self.keep_alive: bool = True
        self._connection_pool: Dict[str, asyncio.StreamWriter] = {}
        self._reader_pool: Dict[str, asyncio.StreamReader] = {}

    def _make_key(self, host: str, port: int) -> str:
        """Создаёт уникальный ключ для пары хост:порт"""
        return f"{host}:{port}"

    async def open_connection(
        self, host: str, port: int
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        Открывает новое асинхронное соединение с сервером

        Args:
            host: IP-адрес или домен сервера
            port: Номер порта

        Returns:
            Кортеж (reader, writer) для асинхронного обмена данными
        """
        try:
            reader, writer = await asyncio.open_connection(host, port)
            key = self._make_key(host, port)
            self._connection_pool[key] = writer
            self._reader_pool[key] = reader
            return reader, writer
        except Exception as e:
            raise ConnectionError(
                f"Не удалось подключиться к {host}:{port} - {e}")

    def get_connection(
        self, host: str, port: int
    ) -> Optional[Tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
        """
        Возвращает сохранённое соединение из пула

        Returns:
            Кортеж (reader, writer) или None
        """
        if not self.keep_alive:
            return None

        key = self._make_key(host, port)
        writer = self._connection_pool.get(key)
        reader = self._reader_pool.get(key)

        if writer and not writer.is_closing():
            return reader, writer
        elif writer:
            self.close_connection(host, port)

        return None

    def save_connection(
        self,
        host: str,
        port: int,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Сохраняет соединение в пул для будущего использования"""
        if not self.keep_alive:
            writer.close()
            return

        key = self._make_key(host, port)
        self._connection_pool[key] = writer
        self._reader_pool[key] = reader

    def close_connection(self, host: str, port: int) -> None:
        """Закрывает соединение и удаляет его из пула"""
        key = self._make_key(host, port)
        writer = self._connection_pool.get(key)
        if writer:
            try:
                writer.close()
            except Exception:
                pass
            if key in self._connection_pool:
                del self._connection_pool[key]
            if key in self._reader_pool:
                del self._reader_pool[key]

    def close_all(self) -> None:
        """Закрывает все соединения в пуле"""
        for writer in self._connection_pool.values():
            try:
                writer.close()
            except Exception:
                pass
        self._connection_pool.clear()
        self._reader_pool.clear()
