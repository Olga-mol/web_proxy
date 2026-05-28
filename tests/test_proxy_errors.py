"""Юнит тесты для ошибок прокси"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from exceptions import (
    ProxyError,
    BadRequestException,
    ConnectionRefusedException,
    TimeoutException,
)


class TestProxyError:

    def test_proxy_error_stores_error_code_and_message(self):
        err = ProxyError(500, "Internal error")
        assert err.error_code == 500
        assert err.message == "Internal error"
        assert str(err) == "Internal error"

    def test_proxy_error_returns_error_code_via_method(self):
        err = ProxyError(403, "Forbidden")
        assert err.get_error_code() == 403


class TestBadRequestException:

    def test_bad_request_has_code_400(self):
        err = BadRequestException("Invalid syntax")
        assert err.error_code == 400
        assert "Invalid syntax" in str(err)


class TestConnectionRefusedException:

    def test_connection_refused_has_code_502(self):
        err = ConnectionRefusedException("google.com", 80)
        assert err.error_code == 502
        assert "google.com" in str(err)
        assert "80" in str(err)


class TestTimeoutException:

    def test_timeout_has_code_504(self):
        err = TimeoutException(30000)
        assert err.error_code == 504
        assert "30000" in str(err)


class TestInheritance:

    def test_all_exceptions_inherit_from_proxy_error(self):
        assert issubclass(BadRequestException, ProxyError)
        assert issubclass(ConnectionRefusedException, ProxyError)
        assert issubclass(TimeoutException, ProxyError)
