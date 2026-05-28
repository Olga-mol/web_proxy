"""Юнит тесты для Logger"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
from interface.logger import Logger


class TestLogger:

    def setup_method(self):
        self.logger = Logger()

    def test_init_creates_logger_with_correct_name(self):
        assert self.logger.logger.name == "WebProxy"

    def test_log_calls_logger_info(self):
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log("Test message")
            mock_info.assert_called_once_with("Test message")

    def test_log_request_formats_correctly(self):
        with patch.object(self.logger, "log") as mock_log:
            self.logger.log_request(
                client_ip="127.0.0.1",
                method="GET",
                url="example.com/",
                status_code=200,
                bytes_transferred=12560,
                processing_time_ms=150,
            )
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "127.0.0.1" in call_args
            assert "GET" in call_args
            assert "200" in call_args

    def test_log_request_with_post_method(self):
        with patch.object(self.logger, "log") as mock_log:
            self.logger.log_request(
                client_ip="192.168.1.1",
                method="POST",
                url="api.example.com/data",
                status_code=201,
                bytes_transferred=512,
                processing_time_ms=45,
            )
            call_args = mock_log.call_args[0][0]
            assert "POST" in call_args
            assert "201" in call_args

    def test_log_request_with_error_status(self):
        with patch.object(self.logger, "log") as mock_log:
            self.logger.log_request(
                client_ip="10.0.0.1",
                method="GET",
                url="example.com/notfound",
                status_code=404,
                bytes_transferred=1024,
                processing_time_ms=10,
            )
            call_args = mock_log.call_args[0][0]
            assert "404" in call_args

    def test_log_request_with_https_connect(self):
        with patch.object(self.logger, "log") as mock_log:
            self.logger.log_request(
                client_ip="127.0.0.1",
                method="CONNECT",
                url="google.com:443",
                status_code=200,
                bytes_transferred=0,
                processing_time_ms=50,
            )
            call_args = mock_log.call_args[0][0]
            assert "CONNECT" in call_args
            assert "google.com:443" in call_args

    def test_close_calls_logging_shutdown(self):
        with patch("logging.shutdown") as mock_shutdown:
            self.logger.close()
            mock_shutdown.assert_called_once()

    def test_log_writes_to_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            test_logger = Logger(log_file=tmp_path)
            test_logger.log("Test file log message")
            test_logger.close()

            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "Test file log message" in content
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
