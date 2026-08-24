"""datasources.terrain.elevation — ความสูงจาก SRTM ผ่าน OpenTopoData (ฟรี ไม่ต้องคีย์, Ticket 12)

ใช้เป็นกริดหลายจุด → NormalizedRow(value=เมตร) สำหรับทำ mountain ranking
"""
from __future__ import annotations

import time

import requests

from core import cache as core_cache
from core.geometry import bbox_grid
from core.normalize import NormalizedRow, from_dict, make, to_records

BASE = "https://api.opentopodata.org/v1/srtm90m"
PER_POINT_TTL = 3600 * 24 * 30  # SRTM ไม่เปลี่ยน — cache 30 วัน
DELAY = 1.1  # วินาที/จุด — OpenTopoData จำกัด ~1 req/วินาที


def _elev(lat, lon, _tries=3) -> float | None:
    for attempt in range(_tries):
        r = requests.get(BASE, params={"locations": f"{lat},{lon}"}, timeout=30)
        if r.status_code == 429:
            time.sleep(1.5 * (attempt + 1))
            continue
        r.raise_for_status()
        d = r.json()
        try:
            return float(d["results"][0]["elevation"])
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    return None


def point(lat, lon, use_cache=True, ttl=PER_POINT_TTL) -> NormalizedRow | None:
    cv = core_cache.JSONCache(ttl=ttl)
    key = f"opentopo_elev::{lat}:{lon}"
    if use_cache:
        cached = cv.get(key)
        if cached is not None:
            return from_dict(cached)
    v = _elev(lat, lon)
    if v is None:
        return None
    row = make(lat, lon, "static", "elevation_m", v, "srtm90m", {"dataset": "srtm90m"})
    cv.set(key, row.to_dict())
    return row


def grid(bbox, step_km: float = 15.0, use_cache=True) -> list[NormalizedRow]:
    """กริดความสูงทั่ว bbox ที่เซ็ตห่าง step_km กม. → list[NormalizedRow]."""
    rows = []
    for lat, lon in bbox_grid(bbox, step_km=step_km):
        r = point(lat, lon, use_cache=use_cache)
        if r is not None:
            rows.append(r)
        time.sleep(DELAY)
    return rows