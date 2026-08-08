"""Точка входа в асинхронный web-прокси"""

import sys
import asyncio
import os
from interface import ProxyServer


def print_help() -> None:
    """Выводит справочную информацию из файла help.txt"""
    help_file_path = os.path.join(os.path.dirname(__file__), "help.txt")

    try:
        with open(help_file_path, "r", encoding="utf-8") as f:
            print(f.read())
    except FileNotFoundError:
        exit(0)


async def main_async(port: int) -> None:
    """
    Асинхронная главная функция программы

    Args:
        port: Номер порта для прокси-сервера
    """
    server = ProxyServer(port=port, max_workers=100)

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nОстановка сервера...")
        server.stop()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(4)


def main() -> None:
    """Точка входа - обрабатывает аргументы командной строки"""
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit(0)

    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                print("Ошибка: порт должен быть в диапазоне от 1 до 65535")
                print("Использование: python main.py [порт]")
                print("Для справки: python main.py --help")
                sys.exit(1)
        except ValueError:
            print(
                f"Ошибка: '{sys.argv[1]}' не "
                f"является допустимым номером порта")
            print("Использование: python main.py [порт]")
            print("Для справки: python main.py --help")
            sys.exit(1)

    try:
        asyncio.run(main_async(port))
    except KeyboardInterrupt:
        print("\nПрограмма завершена")
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
