"""datasources.met.open_meteo — สภาพอากาศจาก Open-Meteo (ฟรี ไม่ต้องคีย์, Ticket 06)

- `current(lat, lon)` → อุณหภูมิ/ความเร็วลมปัจจุบัน เป็น NormalizedRow
- `hourly_range(lat, lon, start, end)` → อนุกรมรายชั่วโมง (metric 'openmeteo_<var>')
"""
from __future__ import annotations

import requests

from core import cache as core_cache
from core.normalize import NormalizedRow, from_dict, make, to_records

BASE = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TTL = 3600

_CURRENT_VARS = {
    "temperature": "openmeteo_temperature",
    "windspeed": "openmeteo_windspeed",
    "winddirection": "openmeteo_winddirection",
}
_HOURLY_VARS = {
    "temperature_2m": "openmeteo_temperature",
    "relative_humidity_2m": "openmeteo_rh",
    "precipitation": "openmeteo_precipitation",
    "wind_speed_10m": "openmeteo_windspeed",
}


def current(lat, lon, use_cache=True, ttl=DEFAULT_TTL) -> list[NormalizedRow]:
    cv = core_cache.JSONCache(ttl=ttl)
    key = f"openmeteo_current::{lat}:{lon}"
    if use_cache:
        cached = cv.get(key)
        if cached is not None:
            return [from_dict(d) for d in cached]
    r = requests.get(BASE, params={"latitude": lat, "longitude": lon,
                                   "current_weather": "true"}, timeout=30)
    r.raise_for_status()
    d = r.json()["current_weather"]
    rows = [make(lat, lon, d["time"], metric, float(d[v]), "open_meteo")
            for v, metric in _CURRENT_VARS.items() if d.get(v) is not None]
    cv.set(key, to_records(rows))
    return rows


def hourly_range(lat, lon, start, end, use_cache=True, ttl=DEFAULT_TTL) -> list[NormalizedRow]:
    """อนุกรมรายชั่วโมง (เวลาคือ 'YYYY-MM-DDTHH:MM') สำหรับช่วง start→end."""
    cv = core_cache.JSONCache(ttl=ttl)
    key = f"openmeteo_hourly::{lat}:{lon}:{start}:{end}"
    if use_cache:
        cached = cv.get(key)
        if cached is not None:
            return [from_dict(d) for d in cached]
    r = requests.get(BASE, params={
        "latitude": lat, "longitude": lon,
        "hourly": ",".join(_HOURLY_VARS), "start_date": start, "end_date": end,
    }, timeout=30)
    r.raise_for_status()
    hourly = r.json()["hourly"]
    times = hourly.get("time", [])
    rows = []
    for var, metric in _HOURLY_VARS.items():
        for i, t in enumerate(times):
            val = hourly.get(var, [None] * len(times))[i]
            if val is not None:
                rows.append(make(lat, lon, t, metric, float(val), "open_meteo"))
    cv.set(key, to_records(rows))
    return rows