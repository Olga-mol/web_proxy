"""Юнит тесты для setup_proxy.py"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
import setup_proxy


class TestSetupProxy:

    def test_set_windows_proxy_success(self):
        with patch("subprocess.run") as mock_run:
            setup_proxy.set_windows_proxy(8080)
            assert mock_run.call_count == 2

    def test_set_windows_proxy_with_default_port(self):
        with patch("subprocess.run") as mock_run:
            setup_proxy.set_windows_proxy()
            assert mock_run.call_count == 2
            args = mock_run.call_args_list[1][0][0]
            assert "127.0.0.1:8080" in args

    def test_set_windows_proxy_with_custom_port(self):
        with patch("subprocess.run") as mock_run:
            setup_proxy.set_windows_proxy(8888)
            args = mock_run.call_args_list[1][0][0]
            assert "127.0.0.1:8888" in args

    def test_set_windows_proxy_exception_handling(self):
        with patch("subprocess.run", side_effect=Exception("Error")):
            with patch("builtins.print") as mock_print:
                setup_proxy.set_windows_proxy(8080)
                mock_print.assert_called_with("Ошибка настройки прокси: Error")

    def test_clear_windows_proxy_success(self):
        with patch("subprocess.run") as mock_run:
            setup_proxy.clear_windows_proxy()
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ProxyEnable" in args
            assert "0" in args

    def test_clear_windows_proxy_exception_handling(self):
        with patch("subprocess.run", side_effect=Exception("Error")):
            with patch("builtins.print") as mock_print:
                setup_proxy.clear_windows_proxy()
                mock_print.assert_called_with("Ошибка отключения прокси: Error")
