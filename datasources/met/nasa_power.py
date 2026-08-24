"""datasources.met.nasa_power — สภาพอากาศจาก NASA POWER API (ฟรี ไม่ต้องคีย์, Ticket 05)

- จุดเดียว/กริด: `fetch_point(lat, lon, start, end, params)`
- เอาพารามิเตอร์ (T2M อุณหภูมิ, PRECTOTCORR ฝน, RH2M ความชื้น …) เป็น NormalizedRow
- cache ตาม (จุด,ช่วง,params)
"""
from __future__ import annotations

import requests

from core import cache as core_cache
from core.normalize import NormalizedRow, from_dict, make, to_records

BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"
DEFAULT_TTL = 3600 * 6  # 6 ชม.
DEFAULT_PARAMS = ("T2M", "PRECTOTCORR", "RH2M")


def _compact(date: str) -> str:
    """'2023-04-01' → '20230401' (NASA POWER รับ YYYYMMDD เท่านั้น)."""
    return date.replace("-", "")


def _fetch(lat, lon, start, end, params, community="ag"):
    r = requests.get(BASE, params={
        "parameters": ",".join(params), "community": community,
        "longitude": lon, "latitude": lat, "start": _compact(start), "end": _compact(end),
        "format": "JSON",
    }, timeout=45)
    r.raise_for_status()
    return r.json()["properties"]["parameter"]


def _iso_time(t: str) -> str:
    """'20230401' → '2023-04-01' (NASA POWER คืน YYYYMMDD); ถ้าเป็น ISO แล้วปล่อยไว้."""
    t = str(t)
    if len(t) == 8 and t.isdigit():
        return f"{t[0:4]}-{t[4:6]}-{t[6:8]}"
    return t


def _rows_from_series(lat, lon, series, src_metric_prefix):
    """{ 'T2M': {'20230401': 30.2, ...}, ... } → rows (metric='power_<PARAM>', time ISO)."""
    rows = []
    for param, daymap in series.items():
        for date, val in daymap.items():
            if val is None:
                continue
            rows.append(make(lat, lon, _iso_time(date), f"{src_metric_prefix}_{param}",
                             float(val), "nasa_power"))
    return rows


def fetch_point(lat, lon, start, end, params=DEFAULT_PARAMS,
                community="ag", use_cache=True, ttl=DEFAULT_TTL) -> list[NormalizedRow]:
    cv = core_cache.JSONCache(ttl=ttl)
    key = f"nasa_power::{lat}:{lon}:{start}:{end}:{','.join(params)}"
    if use_cache:
        cached = cv.get(key)
        if cached is not None:
            return [from_dict(d) for d in cached]
    series = _fetch(lat, lon, start, end, params, community)
    rows = _rows_from_series(lat, lon, series, "power")
    cv.set(key, to_records(rows))
    return rows


def grid(bbox, start, end, params=DEFAULT_PARAMS, step_km=25.0, community="ag") -> list[NormalizedRow]:
    """กริดหลายจุดใน bbox → รวม NormalizedRow ทุกจุด (รอบขั้นตอน API ต่างกัน)."""
    from core.geometry import bbox_grid
    rows = []
    for lat, lon in bbox_grid(bbox, step_km=step_km):
        rows.extend(fetch_point(lat, lon, start, end, params, community=community))
    return rows