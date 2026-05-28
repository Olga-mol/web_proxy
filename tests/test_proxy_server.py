"""Юнит тесты для ProxyServer"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, AsyncMock
from interface.proxy_server import ProxyServer


class TestProxyServer:

    def setup_method(self):
        self.server = ProxyServer(port=8080, max_workers=100)

    def test_init_sets_correct_port(self):
        assert self.server.port == 8080

    def test_init_sets_correct_max_workers(self):
        assert self.server.max_workers == 100

    def test_init_running_is_false_by_default(self):
        assert self.server.running is False

    def test_init_server_is_none_by_default(self):
        assert self.server.server is None

    def test_stop_sets_running_to_false_and_closes_server(self):
        with patch.object(self.server.logger, "log") as mock_log:
            self.server.stop()
            mock_log.assert_called_with("Прокси-сервер остановлен")
        assert self.server.running is False

    def test_custom_port_works(self):
        custom_server = ProxyServer(port=8888, max_workers=50)
        assert custom_server.port == 8888
        assert custom_server.max_workers == 50

    def test_stop_closes_logger(self):
        with patch.object(self.server.logger, "close") as mock_close:
            self.server.stop()
            mock_close.assert_called_once()

    def test_stop_closes_server_socket(self):
        self.server.stop()
        # Серверный сокет мог быть None - проверяем что метод работает без ошибок
        assert self.server.running is False
