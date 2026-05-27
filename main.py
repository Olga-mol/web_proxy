"""Точка входа в программу web-прокси"""

import sys
from interface import ProxyServer


def main() -> None:
    """
    Главная функция программы

    Считывает порт из аргументов командной строки,
    создаёт и запускает прокси-сервер
    """
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Неверный порт. Использую порт 8080")

    server = ProxyServer(port=port, max_workers=100)
    server.start()


if __name__ == "__main__":
    main()