"""Юнит тесты для RequestHandler (только синхронные методы)"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock
from core.request_handler import RequestHandler
from interface.logger import Logger
from exceptions import BadRequestException


class TestRequestHandlerUnit:

    def setup_method(self):
        self.mock_reader = Mock()
        self.mock_writer = Mock()
        self.mock_writer.get_extra_info.return_value = ("127.0.0.1", 12345)
        self.mock_logger = Mock(spec=Logger)
        self.handler = RequestHandler(
            self.mock_reader, self.mock_writer, self.mock_logger
        )

    def test_init_sets_client_ip(self):
        assert self.handler.client_ip == "127.0.0.1"

    def test_parse_headers_returns_dict(self):
        lines = ["Host: example.com", "User-Agent: Mozilla/5.0", ""]
        headers = self.handler._parse_headers(lines)
        assert headers["Host"] == "example.com"
        assert headers["User-Agent"] == "Mozilla/5.0"

    def test_parse_headers_empty_returns_empty_dict(self):
        headers = self.handler._parse_headers([])
        assert headers == {}

    def test_parse_headers_ignores_lines_without_colon(self):
        lines = ["Host: example.com", "InvalidLine", "Accept: */*", ""]
        headers = self.handler._parse_headers(lines)
        assert headers["Host"] == "example.com"
        assert headers["Accept"] == "*/*"
        assert "InvalidLine" not in headers

    def test_extract_host_port_from_absolute_url_with_port(self):
        headers = {}
        host, port = self.handler._extract_host_port(
            "http://example.com:8080/page", headers
        )
        assert host == "example.com"
        assert port == 8080

    def test_extract_host_port_from_absolute_url_default_port(self):
        headers = {}
        host, port = self.handler._extract_host_port("http://example.com/page", headers)
        assert host == "example.com"
        assert port == 80

    def test_extract_host_port_from_headers_with_port(self):
        headers = {"Host": "example.com:8080"}
        host, port = self.handler._extract_host_port("/page", headers)
        assert host == "example.com"
        assert port == 8080

    def test_extract_host_port_from_headers_without_port(self):
        headers = {"Host": "example.com"}
        host, port = self.handler._extract_host_port("/page", headers)
        assert host == "example.com"
        assert port == 80

    def test_extract_host_port_raises_exception_when_no_host(self):
        headers = {}
        with pytest.raises(BadRequestException):
            self.handler._extract_host_port("/page", headers)

    def test_extract_path_from_absolute_url(self):
        path = self.handler._extract_path("http://example.com/index.html")
        assert path == "/index.html"

    def test_extract_path_from_absolute_url_root(self):
        path = self.handler._extract_path("http://example.com/")
        assert path == "/"

    def test_extract_path_from_relative_url(self):
        path = self.handler._extract_path("/index.html")
        assert path == "/index.html"

    def test_extract_path_without_slash(self):
        path = self.handler._extract_path("index.html")
        assert path == "index.html"

    def test_extract_status_code_200(self):
        response = "HTTP/1.1 200 OK\r\n\r\n"
        code = self.handler._extract_status_code(response)
        assert code == 200

    def test_extract_status_code_301(self):
        response = "HTTP/1.1 301 Moved Permanently\r\n\r\n"
        code = self.handler._extract_status_code(response)
        assert code == 301

    def test_extract_status_code_404(self):
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        code = self.handler._extract_status_code(response)
        assert code == 404

    def test_extract_status_code_500(self):
        response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
        code = self.handler._extract_status_code(response)
        assert code == 500

    def test_extract_status_code_returns_zero_for_invalid_response(self):
        response = "Invalid response"
        code = self.handler._extract_status_code(response)
        assert code == 0

    def test_build_error_response_string_404(self):
        response = self.handler._build_error_response_string(404, "Not Found")
        assert "404 Not Found" in response
        assert "HTTP/1.1" in response

    def test_build_error_response_string_502(self):
        response = self.handler._build_error_response_string(502, "Bad Gateway")
        assert "502 Bad Gateway" in response
