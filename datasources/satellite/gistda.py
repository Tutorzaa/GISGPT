"""datasources.satellite.gistda — hotspot จาก GISTDA (เปิดสาธารณะ ไม่ต้องคีย์, Ticket 04)

แปลง `geo/hotspots.fetch_gistda` ให้เป็น NormalizedRow ชุดเดียว
พร้อม cache 1 ชม. (core.cache)
"""
from __future__ import annotations

from core import cache as core_cache
from core.normalize import NormalizedRow, from_dict, make, to_records
from geo import hotspots as _hs

DEFAULT_TTL = 3600  # วินาที

_META_KEYS = ("confidence", "satellite", "lu_name", "province", "district", "subdistrict", "frp")


def hotspot_rows(bbox, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[NormalizedRow]:
    """hotspot ใน bbox → NormalizedRow (metric='hotspot_conf', src='gistda')."""
    cv = core_cache.JSONCache(ttl=ttl)
    key = f"gistda_hotspot::{','.join(str(b) for b in bbox)}"
    if use_cache:
        cached = cv.get(key)
        if cached is not None:
            return [from_dict(d) for d in cached]

    raw = _hs.fetch_gistda(bbox)
    rows = []
    for h in raw:
        # ค่าความรุนแรง: ใช้ confidence (GISTDA ไม่มี FRP เสมอ)
        value = h.get("confidence") or h.get("frp") or 0.0
        rows.append(make(
            lat=h["lat"], lon=h["lon"],
            time=str(h.get("datetime") or "")[:10],
            metric="hotspot_conf", value=value, src="gistda",
            meta={k: h.get(k) for k in _META_KEYS if h.get(k) is not None},
        ))
    cv.set(key, to_records(rows))
    return rows