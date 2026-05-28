"""Юнит тесты для DnsResolver (только синхронные методы)"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dns_server import DnsResolver


class TestDnsResolver:

    def setup_method(self):
        self.resolver = DnsResolver()

    def test_init_creates_empty_cache(self):
        assert self.resolver._cache == {}

    def test_cache_is_dict(self):
        assert isinstance(self.resolver._cache, dict)

    def test_lock_exists(self):
        assert hasattr(self.resolver, "_lock")

    def test_cache_stores_domain_ip_pair(self):
        self.resolver._cache["google.com"] = "142.250.185.46"
        assert "google.com" in self.resolver._cache
        assert self.resolver._cache["google.com"] == "142.250.185.46"

    def test_cache_can_store_multiple_entries(self):
        self.resolver._cache["google.com"] = "142.250.185.46"
        self.resolver._cache["yandex.ru"] = "77.88.55.88"
        assert len(self.resolver._cache) == 2
