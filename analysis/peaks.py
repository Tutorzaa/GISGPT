"""analysis.peaks — หาจุดยอดสูงสุด (local maxima) จากกริดความสูง (Ticket 12)

จุดคือ "ยอด" ถ้าความสูง >= ทุกจุดที่อยู่ห่างไม่เกิน neighbor_km
แล้วจัดอันดับจากสูงไปต่ำ + กรองตามความนูน (prominence, อย่างง่าย)
"""
from __future__ import annotations

from core.geometry import haversine


def find_peaks(rows, min_elev: float = 400.0, neighbor_km: float = 25.0,
               min_prominence: float = 0.0, top_n: int = 10) -> list[dict]:
    """rows: list[NormalizedRow] (value = ความสูง เมตร) →
    list[{lat, lon, elev, prominence}] เรียงจากสูง→ต่ำ"""
    out = []
    for p in rows:
        e = p.value
        if e < min_elev:
            continue
        lower_than = None
        for q in rows:
            if q is p:
                continue
            if haversine(p.lat, p.lon, q.lat, q.lon) <= neighbor_km and q.value > e:
                lower_than = q.value
                break
        if lower_than is None:
            out.append({"lat": p.lat, "lon": p.lon, "elev": float(e),
                        "prominence": float(e) - (lower_than or 0.0)})
    out.sort(key=lambda d: -d["elev"])
    out = [d for d in out if d["prominence"] >= min_prominence]
    return out[:top_n]