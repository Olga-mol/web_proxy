"""Юнит тесты для HttpClient (только синхронные методы)"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import inspect
from core.http_client import HttpClient


class TestHttpClientUnit:

    def setup_method(self):
        self.client = HttpClient()

    def test_constants_are_set_correctly(self):
        assert self.client.TIMEOUT_MS == 30000
        assert self.client.BUFFER_SIZE == 8192

    def test_timeout_ms_is_positive_integer(self):
        assert isinstance(self.client.TIMEOUT_MS, int)
        assert self.client.TIMEOUT_MS > 0

    def test_buffer_size_is_positive_integer(self):
        assert isinstance(self.client.BUFFER_SIZE, int)
        assert self.client.BUFFER_SIZE > 0

    def test_buffer_size_is_reasonable(self):
        assert self.client.BUFFER_SIZE in [1024, 2048, 4096, 8192, 16384]

    def test_class_has_send_and_receive_method(self):
        assert hasattr(self.client, "send_and_receive")
        assert callable(self.client.send_and_receive)

    def test_timeout_ms_converted_correctly_to_seconds(self):
        timeout_seconds = self.client.TIMEOUT_MS / 1000
        assert timeout_seconds == 30

    def test_timeout_value_is_reasonable(self):
        assert 10000 <= self.client.TIMEOUT_MS <= 60000

    def test_send_and_receive_method_signature(self):
        sig = inspect.signature(self.client.send_and_receive)
        params = list(sig.parameters.keys())
        assert "reader" in params
        assert "writer" in params
        assert "request" in params
