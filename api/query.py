"""api.query — POST /api/query (Ticket 18)

จุดเข้าเดียว: ส่งข้อความภาษาไทย/อังกฤษ → agent วางแผน + รัน tools
→ คืน {reply, data_points[], layers[], chart?, legend?, artifacts[]}

พารามิเตอร์เสริมใน JSON:
  bbox=[lon_min,lat_min,lon_max,lat_max]  (ถ้าไม่ให้ ใช้ค่า DEFAULT_BBOX ใน tool)
  start/end / radius_km  ส่งต่อให้ tool
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from agent import Agent, memory

bp = Blueprint("api_query", __name__)
_agent = Agent()


@bp.post("/api/query")
def query():
    d = request.get_json(silent=True) or {}
    text = (d.get("text") or "").strip()
    if not text:
        return jsonify(error="Field 'text' is required"), 400
    extras = d.get("query") or {}
    ctx = memory.get("api_query_session")
    ctx["query"] = extras
    try:
        out = _agent.handle("api_query_session", text)
    except Exception as e:  # don't let one query break the API
        return jsonify(error=f"Internal error: {e}"), 500
    return jsonify(out)