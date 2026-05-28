"""Юнит тесты для ConnectionManager"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from core.connection_manager import ConnectionManager


class TestConnectionManager:

    def setup_method(self):
        self.manager = ConnectionManager()

    def test_init_sets_default_values(self):
        assert self.manager.keep_alive is True
        assert self.manager._connection_pool == {}
        assert self.manager._reader_pool == {}

    def test_make_key_returns_host_port_string(self):
        key = self.manager._make_key("google.com", 80)
        assert key == "google.com:80"

    def test_make_key_with_different_port(self):
        key = self.manager._make_key("yandex.ru", 443)
        assert key == "yandex.ru:443"

    def test_get_connection_returns_none_when_keep_alive_disabled(self):
        self.manager.keep_alive = False
        result = self.manager.get_connection("google.com", 80)
        assert result is None

    def test_get_connection_returns_none_when_no_connection(self):
        result = self.manager.get_connection("google.com", 80)
        assert result is None

    def test_save_connection_adds_to_pool(self):
        mock_reader = Mock()
        mock_writer = Mock()
        self.manager.save_connection("google.com", 80, mock_reader, mock_writer)
        assert self.manager._connection_pool["google.com:80"] == mock_writer
        assert self.manager._reader_pool["google.com:80"] == mock_reader

    def test_save_connection_closes_writer_when_keep_alive_disabled(self):
        self.manager.keep_alive = False
        mock_reader = Mock()
        mock_writer = Mock()
        self.manager.save_connection("google.com", 80, mock_reader, mock_writer)
        mock_writer.close.assert_called_once()
        assert self.manager._connection_pool == {}

    def test_get_connection_returns_existing_connection_when_alive(self):
        mock_reader = Mock()
        mock_writer = Mock()
        mock_writer.is_closing.return_value = False
        key = "google.com:80"
        self.manager._connection_pool[key] = mock_writer
        self.manager._reader_pool[key] = mock_reader

        result = self.manager.get_connection("google.com", 80)
        assert result is not None
        reader, writer = result
        assert reader == mock_reader
        assert writer == mock_writer

    def test_get_connection_removes_dead_connection(self):
        mock_writer = Mock()
        mock_writer.is_closing.return_value = True
        key = "google.com:80"
        self.manager._connection_pool[key] = mock_writer
        self.manager._reader_pool[key] = Mock()

        result = self.manager.get_connection("google.com", 80)
        assert result is None
        assert key not in self.manager._connection_pool

    def test_close_connection_removes_existing_connection(self):
        mock_writer = Mock()
        mock_reader = Mock()
        self.manager._connection_pool["google.com:80"] = mock_writer
        self.manager._reader_pool["google.com:80"] = mock_reader
        self.manager.close_connection("google.com", 80)
        mock_writer.close.assert_called_once()
        assert "google.com:80" not in self.manager._connection_pool
        assert "google.com:80" not in self.manager._reader_pool

    def test_close_connection_does_nothing_for_nonexistent_connection(self):
        self.manager.close_connection("unknown.com", 80)

    def test_close_all_clears_all_connections(self):
        self.manager._connection_pool["google.com:80"] = Mock()
        self.manager._connection_pool["yandex.ru:443"] = Mock()
        self.manager.close_all()
        assert self.manager._connection_pool == {}
        assert self.manager._reader_pool == {}
