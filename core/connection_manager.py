"""Модуль для управления соединениями (Keep-Alive)"""

import socket
from threading import Lock
from typing import Optional, Dict


class ConnectionManager:
    """
    Управляет пулом постоянных соединений для Keep-Alive.

    Позволяет переиспользовать открытые соединения к одним и тем же серверам,
    что ускоряет последующие запросы
    """

    def __init__(self) -> None:
        """Инициализация менеджера соединений"""
        self.keep_alive: bool = True
        self._connection_pool: Dict[str, socket.socket] = {}
        self._lock: Lock = Lock()

    def _make_key(self, host: str, port: int) -> str:
        """
        Создаёт уникальный ключ для пары хост:порт

        Args:
            host: Имя хоста
            port: Номер порта

        Returns:
            Строка вида "host:port"
        """
        return f"{host}:{port}"

    def open_connection(self, host: str, port: int) -> socket.socket:
        """
        Открывает новое соединение с сервером и сохраняет в пул

        Args:
            host: IP-адрес или домен сервера
            port: Номер порта

        Returns:
            Созданный сокет
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((host, port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        key = self._make_key(host, port)
        with self._lock:
            self._connection_pool[key] = sock

        return sock

    def get_connection(self, host: str, port: int) -> Optional[socket.socket]:
        """
        Возвращает сохранённое соединение из пула, если оно есть и живо

        Args:
            host: Имя хоста
            port: Номер порта

        Returns:
            Сокет из пула или None, если соединения нет
        """
        if not self.keep_alive:
            return None

        key = self._make_key(host, port)
        with self._lock:
            sock = self._connection_pool.get(key)

        if sock and self._is_connection_alive(sock):
            return sock
        elif sock:
            self.close_connection(sock)

        return None

    def save_connection(self, host: str, port: int, sock: socket.socket) -> None:
        """
        Сохраняет соединение в пул для будущего использования

        Args:
            host: Имя хоста
            port: Номер порта
            sock: Сокет для сохранения
        """
        if not self.keep_alive:
            sock.close()
            return

        key = self._make_key(host, port)
        with self._lock:
            self._connection_pool[key] = sock

    def close_connection(self, sock: socket.socket) -> None:
        """
        Закрывает соединение и удаляет его из пула

        Args:
            sock: Сокет для закрытия
        """
        try:
            sock.close()
        except Exception:
            pass

        with self._lock:
            for key, s in list(self._connection_pool.items()):
                if s == sock:
                    del self._connection_pool[key]
                    break

    def close_all(self) -> None:
        """Закрывает все соединения в пуле и очищает его"""
        with self._lock:
            for sock in self._connection_pool.values():
                try:
                    sock.close()
                except Exception:
                    pass
            self._connection_pool.clear()

    @staticmethod #че...?
    def _is_connection_alive(sock: socket.socket) -> bool:
        """
        Проверяет, живо ли соединение

        Args:
            sock: Сокет для проверки

        Returns:
            True если соединение живо, False в противном случае
        """
        try:
            sock.getpeername()
            return True
        except Exception:
            return False