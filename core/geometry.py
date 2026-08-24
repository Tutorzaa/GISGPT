"""core.geometry — เครื่องมือเรขาคณิต (Ticket 02)

bbox ใช้แบบ `(min_lon, min_lat, max_lon, max_lat)` (ลำดับ x,y = lon,lat เหมือน GeoJSON)
"""
from __future__ import annotations

import math
from typing import Optional

_R = 6371.0  # รัศมีโลก km


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """ระยะทางใหญ่ (km) ระหว่าง 2 พิกัด."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _R * math.asin(math.sqrt(h))


def bbox_center(bbox) -> tuple[float, float]:
    """จุดกึ่งกลาง bbox → (lat, lon)."""
    min_lon, min_lat, max_lon, max_lat = _unpack(bbox)
    return (min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0


def _unpack(bbox):
    if len(bbox) != 4:
        raise ValueError("bbox ต้องเป็น (min_lon, min_lat, max_lon, max_lat)")
    return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])


def _lat_step(km: float) -> float:
    return km / 111.32


def _lon_step(km: float, mid_lat: float) -> float:
    return km / (111.32 * max(math.cos(math.radians(mid_lat)), 0.05))


def bbox_grid(bbox, step_km: float = 10.0):
    """สร้างกริดจุดศูนย์กลางใน bbox ห่างกัน step_km → list[(lat, lon)]."""
    min_lon, min_lat, max_lon, max_lat = _unpack(bbox)
    mid_lat = (min_lat + max_lat) / 2.0
    dlat, dlon = _lat_step(step_km), _lon_step(step_km, mid_lat)
    pts = []
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            pts.append((round(lat, 6), round(lon, 6)))
            lon += dlon
        lat += dlat
    return pts


def point_in_polygon(lat: float, lon: float, geom) -> bool:
    """จุดอยู่ในโพลิกอนหรือไม่; `geom` เป็น shapely geometry หรือ GeoJSON dict.

    ขอบเขต/ขอบถือนับว่า "ใน"
    """
    shp = _to_shapely(geom)
    return bool(shp.contains(__point(lon, lat)) or shp.intersects(__point(lon, lat)))


def _to_shapely(geom):
    if hasattr(geom, "contains") and hasattr(geom, "intersects"):
        return geom
    from shapely.geometry import shape
    return shape(geom)


def __point(lon, lat):
    from shapely.geometry import Point
    return Point(lon, lat)


def buffer_bbox(lat: float, lon: float, km: float):
    """กล่องรอบจุด (min_lon, min_lat, max_lon, max_lat) ห่างออกไป km (ประมาณ)."""
    dlat = _lat_step(km)
    dlon = _lon_step(km, lat)
    return round(lon - dlon, 6), round(lat - dlat, 6), round(lon + dlon, 6), round(lat + dlat, 6)


def provinces_from_geojson(path: str) -> dict:
    """โหลด GeoJSON อาณาเขต (เช่น thailand.json 77 จว.) → dict {ชื่อ: polygon/shape}."""
    import json
    from shapely.geometry import shape

    with open(path, encoding="utf-8") as fh:
        gj = json.load(fh)
    out = {}
    for f in gj.get("features", []):
        name = f.get("properties", {}).get("name") or f.get("properties", {}).get("NAME_1")
        if name:
            out[name] = _to_shapely(f.get("geometry"))
    return out