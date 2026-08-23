"""GISGPT — Geospatial Foundation Model Agent (Flask web app)

รัน:  python main.py  →  http://localhost:5000
"""
import os
import uuid

from flask import Flask, jsonify, render_template, request, send_from_directory, session

from agent import Agent
from agent import memory as mem
from geo import hotspots as hs
from geo import io as geo_io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS = os.path.join(BASE_DIR, "outputs")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gisgpt-dev-key")
agent = Agent()


@app.before_request
def _ensure_sid():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if f is None or not f.filename:
        return jsonify(error="ไม่พบไฟล์"), 400
    info = geo_io.save_upload(f)
    mem.get(session["sid"])["current"] = info
    mem.get(session["sid"]).pop("last", None)  # ภาพใหม่ → ผลเก่าไม่ถูกต้อง
    return jsonify(info)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(error="ข้อความว่างเปล่า"), 400
    return jsonify(agent.handle(session["sid"], message))


@app.route("/hotspots")
def hotspots_page():
    return render_template("hotspots.html")


@app.route("/api/hotspots")
def api_hotspots():
    province = request.args.get("province", "บุรีรัมย์")
    data = hs.province_hotspots(province)
    if "error" in data:
        return jsonify(data), 404
    return jsonify(data)


@app.route("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(OUTPUTS, name)


if __name__ == "__main__":
    os.makedirs(OUTPUTS, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
