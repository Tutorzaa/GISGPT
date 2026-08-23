"""GISGPT — Geospatial Foundation Model Agent (Flask web app)

รัน:  python main.py  →  http://localhost:5000
"""
import os
import uuid

from flask import Flask, jsonify, render_template, request, send_from_directory, session

from agent import Agent
from agent import memory as mem
from geo import airquality as aq
from geo import analysis as an
from geo import dashboard as dash
from geo import hotspots as hs
from geo import io as geo_io
from landing import landing_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS = os.path.join(BASE_DIR, "outputs")

# โหลด .env (คีย์ API) ถ้ามี
_env = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env):
    for line in open(_env, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

app = Flask(__name__)
app.register_blueprint(landing_bp)
app.secret_key = os.environ.get("SECRET_KEY", "gisgpt-dev-key")
agent = Agent()


@app.before_request
def _ensure_sid():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex


@app.route("/chat")
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


@app.route("/api/airquality")
def api_airquality():
    """สถานีวัดอากาศที่ใกล้จังหวัดที่สุด + ค่า PM2.5/PM10"""
    province = request.args.get("province", "บุรีรัมย์")
    feature, pname = hs.find_province(province)
    if feature is None:
        return jsonify(error=f"ไม่พบจังหวัด '{province}'"), 404
    bbox = hs.province_bbox(feature, margin=0.0)
    lat = (bbox[1] + bbox[3]) / 2
    lon = (bbox[0] + bbox[2]) / 2
    stations = aq.fetch_gistda_aq()
    nearest = an.nearest_stations(lat, lon, stations, k=5)
    return jsonify({"province": pname, "center": {"lat": lat, "lon": lon}, "stations": nearest})


@app.route("/api/correlation")
def api_correlation():
    """ผลลัพธ์ Phase B (จาก scripts/fetch_phaseb.py) — ถ้ายังไม่รันจะบอกวิธี"""
    import glob

    files = sorted(glob.glob(os.path.join(BASE_DIR, "data", "processed", "phaseb_*.json")))
    if not files:
        return jsonify({
            "note": "ยังไม่มีการวิเคราะห์ — รัน `python scripts/fetch_phaseb.py --date 2020-08-29` "
                    "(ต้องมี FIRMS_KEY ใน .env) ก่อน",
            "files": [],
        })
    results = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            results.append(json.load(fh))
    return jsonify({"files": files, "results": results})


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/api/dashboard")
def api_dashboard():
    province = request.args.get("province", "บุรีรัมย์")
    start = request.args.get("start", "2023-04-01")
    end = request.args.get("end", "2023-04-30")
    data = dash.fetch_dashboard(province, start, end)
    if "error" in data:
        return jsonify(data), 404
    return jsonify(data)


@app.route("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(OUTPUTS, name)


if __name__ == "__main__":
    os.makedirs(OUTPUTS, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
