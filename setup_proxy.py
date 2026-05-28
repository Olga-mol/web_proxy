"""Утилита для настройки системного прокси в Windows"""

import subprocess
import sys


def set_windows_proxy(port: int = 8080) -> None:
    """Устанавливает системный прокси в Windows"""
    try:
        subprocess.run(
            [
                "reg",
                "add",
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                "/v",
                "ProxyEnable",
                "/t",
                "REG_DWORD",
                "/d",
                "1",
                "/f",
            ],
            check=True,
        )
        subprocess.run(
            [
                "reg",
                "add",
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                "/v",
                "ProxyServer",
                "/t",
                "REG_SZ",
                "/d",
                f"127.0.0.1:{port}",
                "/f",
            ],
            check=True,
        )
        print(f"Системный прокси установлен на 127.0.0.1:{port}")
    except Exception as e:
        print(f"Ошибка настройки прокси: {e}")


def clear_windows_proxy() -> None:
    """Отключает системный прокси в Windows"""
    try:
        subprocess.run(
            [
                "reg",
                "add",
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                "/v",
                "ProxyEnable",
                "/t",
                "REG_DWORD",
                "/d",
                "0",
                "/f",
            ],
            check=True,
        )
        print("Системный прокси отключён")
    except Exception as e:
        print(f"Ошибка отключения прокси: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "on":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            set_windows_proxy(port)
        elif sys.argv[1] == "off":
            clear_windows_proxy()
        else:
            print("Использование: python setup_proxy.py on [порт]  - включить прокси")
            print("             python setup_proxy.py off          - выключить прокси")
    else:
        print("Использование: python setup_proxy.py on [порт]  - включить прокси")
        print("             python setup_proxy.py off          - выключить прокси")
