# config/settings_override.py
class MockRedis:
    def ping(self): return True
    def get(self, key): return None
    def set(self, key, value): return True
    def from_url(self, *args, **kwargs): return self