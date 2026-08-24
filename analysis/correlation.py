"""analysis.correlation — วิเคราะห์ความสัมพันธ์ระหว่าง 2 metric บน NormalizedRow

- `cross_sectional`: จับคู่จุดในรัศมี (และวันที่ใกล้) → เปรียบเทียบค่าเป็นคู่จุด
- `time_series`: รวมรายวัน (mean ต่อจุด) → เปรียบเทียบเป็นอนุกรมรายวัน

ทั้งสองคืน {r, p, n, points, ...} — ใช้ core.geometry.haversine จับคู่,
คำนวณค่า r/p ผ่าน geo.analysis.pearson (มี fallback ไร้ scipy)
"""
from __future__ import annotations

from datetime import date as _Date

import numpy as np

from core.geometry import haversine
from geo import analysis as _ga


def _d(s) -> _Date | None:
    """'2023-04-01...' → date; ผิดพลาด → None."""
    s = str(s)[:10]
    try:
        return _Date(*map(int, s.split("-")))
    except Exception:
        return None


def match_rows(rows_a, rows_b, radius_km: float = 50.0, date_gap_days: int = 7):
    """จับคู่จุด a ↔ b: เลือก b ที่ใกล้สุดในรัศมี และวันใกล้สุดใน date_gap_days.

    คืน list[(NormalizedRow_a, NormalizedRow_b)]
    """
    pairs = []
    for a in rows_a:
        da = _d(a.time)
        best, best_key = None, None
        for b in rows_b:
            dist = haversine(a.lat, a.lon, b.lat, b.lon)
            if dist > radius_km:
                continue
            db = _d(b.time)
            gap = 0 if (da is None or db is None) else abs((db - da).days)
            if gap > date_gap_days:
                continue
            key = (gap, dist)
            if best_key is None or key < best_key:
                best_key, best = key, b
        if best is not None:
            pairs.append((a, best))
    return pairs


def _vectors(pairs):
    x = [a.value for a, b in pairs]
    y = [b.value for a, b in pairs]
    pts = [{"x": a.value, "y": b.value, "lat": a.lat, "lon": a.lon} for a, b in pairs]
    return x, y, pts


def cross_sectional(rows_a, rows_b, radius_km=50.0, date_gap_days=7,
                    metric_a="a", metric_b="b"):
    pairs = match_rows(rows_a, rows_b, radius_km, date_gap_days)
    if len(pairs) < 3:
        return _empty("cross", len(pairs), metric_a, metric_b,
                      note="Too few matched pairs (n<3) — radius/date window too tight")
    x, y, pts = _vectors(pairs)
    r, p, n = _ga.pearson(x, y)
    return {"mode": "cross", "n": n, "r": r, "p": p, "points": pts,
            "metric_a": metric_a, "metric_b": metric_b,
            "radius_km": radius_km, "date_gap_days": date_gap_days}


def time_series(rows_a, rows_b, metric_a="a", metric_b="b"):
    a = _daily_mean(rows_a)
    b = _daily_mean(rows_b)
    common = sorted(set(a) & set(b))
    if len(common) < 3:
        return _empty("time", len(common), metric_a, metric_b,
                      note="Too few common dates (n<3)")
    x = [a[k] for k in common]
    y = [b[k] for k in common]
    r, p, n = _ga.pearson(x, y)
    pts = [{"date": k, "metric_a": a[k], "metric_b": b[k]} for k in common]
    return {"mode": "time", "n": n, "r": r, "p": p, "points": pts,
            "metric_a": metric_a, "metric_b": metric_b}


def _daily_mean(rows):
    agg = {}
    for r in rows:
        d = _d(r.time)
        if d is None:
            continue
        agg.setdefault(str(d), []).append(r.value)
    return {k: float(np.mean(v)) for k, v in agg.items()}


def _empty(mode, n, metric_a, metric_b, note):
    return {"mode": mode, "n": n, "r": 0.0, "p": 1.0, "points": [],
            "metric_a": metric_a, "metric_b": metric_b, "note": note}


def render_scatter(result, out_path, title="", xlabel="", ylabel=""):
    """วาด scatter ลง PNG (reuse geo.analysis.render_scatter)."""
    return _ga.render_scatter(result, out_path, title, xlabel, ylabel)