"""api.correlation_api — POST /api/correlation (Ticket 09)

ห่วงโซ่แรกที่พิสูจน์ "ดาวเทียม ↔ met": รับ 2 metric + bbox + เวลา
→ ดึงข้อมูลจริงจาก adapters → วิเคราะห์ correlation (cross/time) → คืน r/p + scatter PNG
"""
from __future__ import annotations

import os
import uuid

from flask import Blueprint, jsonify, request

from analysis import correlation as corr
from core.geometry import bbox_center
from datasources import gistda, nasa_power, open_meteo

bp = Blueprint("correlation_api", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS = os.path.join(BASE_DIR, "outputs")

DEFAULT_START, DEFAULT_END = "2023-04-01", "2023-04-30"


def _bbox(q):
    try:
        return [float(q[k]) for k in ("lon_min", "lat_min", "lon_max", "lat_max")]
    except (KeyError, ValueError):
        return None


def _dates(q):
    return q.get("start", DEFAULT_START), q.get("end", DEFAULT_END)


def _rows(metric, bbox, q):
    """ดึง NormalizedRow ตามชื่อ metric (จาก adapters)."""
    m = metric.lower()
    if m in ("hotspot", "hotspot_conf", "gistda_hotspot"):
        return gistda.hotspot_rows(bbox)
    if m in ("power_t2m", "power_t2m_temp", "temperature"):
        # cross-sectional ต้องการค่า met หลายจุด → กริดทั่ว bbox (วันเดียว = โฟกัสเชิงพื้นที่)
        start = q.get("start", DEFAULT_START)
        step_km = float(q.get("grid_km", 30))
        return nasa_power.grid(bbox, start, start, params=("T2M",), step_km=step_km)
    if m in ("openmeteo_temperature", "weather_temperature"):
        lat, lon = bbox_center(bbox)
        return open_meteo.current(lat, lon)
    raise ValueError(f"ไม่รู้จัก metric '{metric}' (hotspot / power_t2m / openmeteo_temperature)")


@bp.route("/api/correlation", methods=["POST"])
def correlate():
    d = request.get_json(silent=True) or request.form.to_dict() or {}
    bbox = _bbox(d)
    metric_a, metric_b = d.get("metric_a"), d.get("metric_b")
    if bbox is None:
        return jsonify(error="ต้องระบุ lon_min, lat_min, lon_max, lat_max"), 400
    if not metric_a or not metric_b:
        return jsonify(error="ต้องระบุ metric_a กับ metric_b"), 400
    mode = (d.get("mode") or "cross").lower()
    radius_km = float(d.get("radius_km", 60))

    try:
        rows_a = _rows(metric_a, bbox, d)
        rows_b = _rows(metric_b, bbox, d)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    if mode == "time":
        res = corr.time_series(rows_a, rows_b, metric_a=metric_a, metric_b=metric_b)
    else:
        res = corr.cross_sectional(rows_a, rows_b, radius_km=radius_km,
                                   metric_a=metric_a, metric_b=metric_b)

    # วาด scatter ถ้ามีข้อมูลพอ
    os.makedirs(OUTPUTS, exist_ok=True)
    png = os.path.join(OUTPUTS, f"corr_{uuid.uuid4().hex[:8]}.png")
    try:
        corr.render_scatter(res, png, title=f"{metric_a} vs {metric_b}",
                            xlabel=metric_a, ylabel=metric_b)
        res["scatter_png"] = "/outputs/" + os.path.basename(png)
    except Exception:
        res["scatter_png"] = None

    res["summary"] = _summarize(res, metric_a, metric_b)
    return jsonify(res)


def _summarize(res, metric_a, metric_b):
    r, p, n = res.get("r"), res.get("p"), res.get("n")
    if n < 3:
        return f"ข้อมูลน้อยเกินไป (n={n}) — ลองขยาย bbox/ช่วงเวลา หรือเพิ่มรัศมี"
    sig = "มีนัยสำคัญ" if p < 0.05 else "ไม่ชัดเจน"
    direction = "สัมพันธ์เชิงบวก" if r > 0.05 else ("สัมพันธ์เชิงลบ" if r < -0.05 else "แทบไม่สัมพันธ์")
    return (f"{metric_a} ↔ {metric_b}: r={r}, p={p} (n={n}) → "
            f"{direction}, {sig} (หมายเหตุ: correlation ≠ causation)")