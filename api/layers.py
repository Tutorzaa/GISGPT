"""api.layers — /api/layers + /api/layers/<name> (Ticket 07)

ให้ frontend/ระบบอื่นดูว่ามี layer อะไร และดึงข้อมูลเป็น GeoJSON data points
สำหรับวาดบนแผนที่. แต่ละ layer มี fetcher → รายการ NormalizedRow → GeoJSON.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from core.geometry import bbox_center
from core.normalize import to_geojson
from datasources import gistda, nasa_power, open_meteo

bp = Blueprint("layers", __name__)

DEFAULT_START = "2023-04-01"
DEFAULT_END = "2023-04-30"

LAYER_META = {
    "hotspot": {"desc": "จุดความร้อนจากดาวเทียม (GISTDA)",
                "kind": "points", "metric": "hotspot_conf", "src": "gistda"},
    "power_t2m": {"desc": "อุณหภูมิรายวัน (NASA POWER)",
                  "kind": "points", "metric": "power_T2M", "src": "nasa_power"},
    "openmeteo_temperature": {"desc": "อุณหภูมิปัจจุบัน (Open-Meteo)",
                              "kind": "points", "metric": "openmeteo_temperature", "src": "open_meteo"},
}


def _bbox(q):
    try:
        return [float(q[k]) for k in ("lon_min", "lat_min", "lon_max", "lat_max")]
    except (KeyError, ValueError):
        return None


def _dates(q):
    return q.get("start", DEFAULT_START), q.get("end", DEFAULT_END)


def _fetch_hotspot(bbox, q):
    return gistda.hotspot_rows(bbox)


def _fetch_power(bbox, q):
    start, end = _dates(q)
    lat, lon = bbox_center(bbox)
    return nasa_power.fetch_point(lat, lon, start, end, params=("T2M",), use_cache=True)


def _fetch_wx(bbox, q):
    lat, lon = bbox_center(bbox)
    return open_meteo.current(lat, lon)


FETCHERS = {
    "hotspot": _fetch_hotspot,
    "power_t2m": _fetch_power,
    "openmeteo_temperature": _fetch_wx,
}


@bp.route("/api/layers")
def layers_list():
    out = [{"name": n, **m} for n, m in LAYER_META.items()]
    return jsonify({"layers": out,
                    "usage": "/api/layers/<name>?lon_min=&lat_min=&lon_max=&lat_max=[&start=&end=]"})


@bp.route("/api/layers/<name>")
def layer_data(name):
    bbox = _bbox(request.args)
    if bbox is None:
        return jsonify(error="ต้องระบุ lon_min, lat_min, lon_max, lat_max"), 400
    fn = FETCHERS.get(name)
    if fn is None:
        return jsonify(error=f"ไม่พบ layer '{name}', ดู /api/layers"), 404
    rows = fn(bbox, request.args)
    return jsonify(to_geojson(rows))