"""geo/dashboard.py — ข้อมูลสำหรับหน้า Dashboard สไตล์ Fire Emissions Watch

รวมข้อมูลจุดความร้อนหลายวัน → สรุป + อนุกรมรายวัน + แยกตามจังหวัด → JSON ให้ frontend
วาดแผนที่ (Leaflet) + กราฟวิเคราะห์ (ECharts) + แชท AI agent
"""
import datetime as dt
import json
import os

from . import airquality as aq
from . import hotspots as hs

PROVINCES = None  # cache 77 จังหวัด


def _load_provinces_shapely():
    """โหลด polygon 77 จังหวัดเป็น shapely (prepared) + ชื่อ → เร็วตอน assign จุด"""
    global PROVINCES
    if PROVINCES is not None:
        return PROVINCES
    from shapely.geometry import shape
    from shapely.prepared import prep

    feats = hs.load_provinces()
    items = []
    for f in feats:
        g = shape(f["geometry"])
        items.append({
            "name": f["properties"]["name"],
            "geom": prep(g),
            "bbox": g.bounds,
        })
    PROVINCES = items
    return PROVINCES


def _assign_province(lat, lon):
    """หาจังหวัดที่ครอบจุด (point-in-polygon ผ่าน shapely) → ชื่อ หรือ '' """
    from shapely.geometry import Point

    p = Point(lon, lat)
    for item in _load_provinces_shapely():
        xmin, ymin, xmax, ymax = item["bbox"]
        if xmin <= lon <= xmax and ymin <= lat <= ymax and item["geom"].contains(p):
            return item["name"]
    return ""


def fetch_dashboard(province_name, start, end):
    """ดึง + รวมข้อมูลจุดความร้อน (FIRMS archive) ช่วงวันที่ → dict สำหรับ dashboard"""
    feature, pname = hs.find_province(province_name)
    if feature is None:
        return {"error": f"ไม่พบจังหวัด '{province_name}'"}

    bbox = hs.province_bbox(feature, margin=0.3)
    boundary = feature

    points = []
    d = dt.date.fromisoformat(start)
    end_d = dt.date.fromisoformat(end)
    while d <= end_d:
        try:
            hs_day, _ = aq.fetch_firms_archive(bbox, d.isoformat())
            points.extend(hs_day)
        except Exception as e:
            print(f"⚠️ {d} error: {e}")
        d += dt.timedelta(days=1)

    # daily aggregate
    daily_map = {}
    for p in points:
        day = (p.get("datetime") or "")[:10]
        row = daily_map.setdefault(day, {"date": day, "count": 0, "sum_frp": 0.0})
        row["count"] += 1
        row["sum_frp"] += p.get("frp", 0)
    daily = [daily_map[k] for k in sorted(daily_map)]

    # summary
    total_frp = round(sum(p.get("frp", 0) for p in points), 1)
    peak = max(daily, key=lambda x: x["sum_frp"]) if daily else None
    summary = {
        "province": pname,
        "start": start, "end": end,
        "total_hotspots": len(points),
        "total_frp": total_frp,
        "active_days": len(daily),
        "peak_day": peak["date"] if peak else "",
        "peak_frp": peak["sum_frp"] if peak else 0,
    }

    # แยกตามจังหวัด (assign จุดใน bbox)
    by_province = {}
    for p in points:
        pv = _assign_province(p["lat"], p["lon"]) or "(นอกไทย/ทะเล)"
        by_province.setdefault(pv, {"province": pv, "count": 0, "sum_frp": 0.0})
        by_province[pv]["count"] += 1
        by_province[pv]["sum_frp"] += p.get("frp", 0)
    provinces = sorted(by_province.values(), key=lambda x: -x["sum_frp"])

    return {
        "boundary": boundary,
        "points": points,  # ลิสต์ dict {lat, lon, frp, confidence, datetime, satellite}
        "daily": daily,
        "summary": summary,
        "by_province": provinces,
    }
