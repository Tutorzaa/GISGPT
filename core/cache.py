"""core.cache — cache แบบ JSON บนดิสก์ (Ticket 01)

ใช้กับทุก data adapter เพื่อลดการโหลดซ้ำจาก API ภายนอก
key โดยพลการ; มี TTL เป็นวินาที (None = ไม่หมดอายุ)
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import config


class JSONCache:
    def __init__(self, cache_dir: str | None = None, ttl: int | None = None):
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.default_ttl = ttl
        os.makedirs(self.cache_dir, exist_ok=True)

    @staticmethod
    def _key(*parts) -> str:
        """สร้างชื่อไฟล์ที่ปลอดภัยจากหลายส่วน (src, metric, bbox, time…)."""
        joined = "::".join(str(p) for p in parts)
        return hashlib.sha1(joined.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> str:
        if not key or any(c in key for c in "/\\\x00"):
            raise ValueError("key ของ cache ต้องเป็นชื่อปลอดภัย (ใช้ _key() แทน)")
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key: str, ttl: int | None = None):
        """คืนค่าถ้าอยู่ใน cache และยังไม่หมดอายุ(TTL); ไม่พบ/หมดอายุ → None."""
        path = self._path(key)
        if not os.path.exists(path):
            return None
        fresh_after = ttl if ttl is not None else self.default_ttl
        if fresh_after is not None:
            age = time.time() - os.path.getmtime(path)
            if age > fresh_after:
                return None
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def set(self, key: str, data) -> None:
        with open(self._path(key), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)

    def clear(self) -> int:
        n = 0
        for f in os.listdir(self.cache_dir):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(self.cache_dir, f))
                    n += 1
                except OSError:
                    pass
        return n