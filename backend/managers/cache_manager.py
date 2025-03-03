import os
import json
import time
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir='.cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_cache(self, key):
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                if time.time() - data['timestamp'] < data['ttl']:
                    return data['value']
        return None
        
    def set_cache(self, key, value, ttl=3600):
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }, f) 