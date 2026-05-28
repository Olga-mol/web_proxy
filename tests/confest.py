"""Конфигурация pytest"""

import sys
import os
import pytest
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")


# Делаем AsyncMock доступным
pytest.AsyncMock = AsyncMock
