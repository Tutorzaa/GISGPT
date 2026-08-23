"""geo.hotspots — จุดความร้อน (hotspot) การเผาไหม้

- ดึงข้อมูลจาก GISTDA (ArcGIS MapServer — เปิดสาธารณะ) + NASA FIRMS (ถ้ามีคีย์)
- กรองจุดที่อยู่ในขอบเขตจังหวัด (point-in-polygon)
- จัดอันดับความรุนแรง (score = FRP ถ้ามี ไม่งั้น confidence)
"""
import json
import math
import os
import time
import urllib.parse

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

PROVINCES_FILE = os.path.join(RAW_DIR, "thailand_provinces.geojson")
CACHE_FILE = os.path.join(PROC_DIR, "hotspots_cache.json")
CACHE_TTL = 3600  # วินาที — รีเฟรชข้อมูลทุก 1 ชม.

GISTDA_BASE = "https://gistdaportal.gistda.or.th/data/rest/services/FR_Fire"

# ชื่อจังหวัดภาษาไทย → อังกฤษ (ใช้กับไฟล์ขอบเขตที่ชื่อเป็นอังกฤษ)
TH_PROVINCE = {
    "บุรีรัมย์": "Buri Ram", "นครราชสีมา": "Nakhon Ratchasima", "ขอนแก่น": "Khon Kaen",
    "สุรินทร์": "Surin", "ร้อยเอ็ด": "Roi Et", "มหาสารคาม": "Maha Sarakham",
    "ศรีสะเกษ": "Si Sa Ket", "อุบลราชธานี": "Ubon Ratchathani", "ยโสธร": "Yasothon",
    "ชัยภูมิ": "Chaiyaphum", "อำนาจเจริญ": "Amnat Charoen", "หนองบัวลำภู": "Nong Bua Lam Phu",
    "อุดรธานี": "Udon Thani", "สกลนคร": "Sakon Nakhon", "นครพนม": "Nakhon Phanom",
    "เลย": "Loei", "กาฬสินธุ์": "Kalasin", "บึงกาฬ": "Bueng Kan",
    "กรุงเทพมหานคร": "Bangkok", "เชียงใหม่": "Chiang Mai", "เชียงราย": "Chiang Rai",
}


def _flatten(coords):
    """แปลง nested coordinates → list จุด [lon, lat]"""
    if isinstance(coords[0], (int, float)):
        return [coords]
    out = []
    for c in coords:
        out.extend(_flatten(c))
    return out


def _epoch_to_iso(ms):
    try:
        return time.strftime("%Y-%m-%d", time.localtime(int(ms) / 1000))
    except Exception:
        return ""


def point_in_polygon(lat, lon, geom):
    """ray casting — เช็คว่าจุดอยู่ใน polygon ไหม (รองรับ Polygon/MultiPolygon)"""
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        return False
    y, x = lat, lon
    for poly in polys:
        inside = False
        for ring in poly:
            n = len(ring)
            j = n - 1
            for i in range(n):
                xi, yi = ring[i]
                xj, yj = ring[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
        if inside:
            return True
    return False


# --------------------------------------------------------------------------
# ขอบเขตจังหวัด
# --------------------------------------------------------------------------
def load_provinces():
    with open(PROVINCES_FILE, encoding="utf-8") as fh:
        return json.load(fh)["features"]


def find_province(name):
    """ค้นหาจังหวัดจากชื่อไทย/อังกฤษ คืน (feature, key) หรือ (None, None)"""
    en = TH_PROVINCE.get(name, name)
    for f in load_provinces():
        pname = f["properties"]["name"]
        if pname.lower() == name.lower() or pname.lower() == en.lower():
            return f, pname
    return None, None


def province_bbox(feature, margin=0.1):
    pts = _flatten(feature["geometry"]["coordinates"])
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return min(lons) - margin, min(lats) - margin, max(lons) + margin, max(lats) + margin


# --------------------------------------------------------------------------
# ดึงข้อมูล GISTDA (เปิดสาธารณะ ไม่ต้องคีย์)
# --------------------------------------------------------------------------
def _query_arcgis(service, bbox):
    url = (
        f"{GISTDA_BASE}/{service}/MapServer/0/query"
        f"?where=1%3D1&geometry={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        f"&geometryType=esriGeometryEnvelope&inSR=4326"
        f"&spatialRel=esriSpatialRelIntersects&outFields=*&f=geojson"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json().get("features", [])


def _norm_daily(p):
    return {
        "lat": p["latitude"], "lon": p["longitude"],
        "confidence": int(p.get("confident") or 0),
        "satellite": p.get("satellite", ""),
        "datetime": _epoch_to_iso(p.get("datetime")),
        "lu_name": p.get("lu_name", ""),
        "province": p.get("pv_tn", ""), "district": p.get("ap_tn", ""), "subdistrict": p.get("tb_tb", ""),
        "source": "gistda",
    }


def _norm_npp(p):
    conf_map = {"low": 40, "nominal": 60, "high": 90}
    sat = "NOAA-20 VIIRS" if p.get("satellite") == "N" else p.get("satellite", "")
    return {
        "lat": p["latitude"], "lon": p["longitude"],
        "confidence": conf_map.get(str(p.get("confident", "")).lower(), 50),
        "satellite": sat,
        "datetime": (_epoch_to_iso(p.get("date")) + " " + (p.get("time") or "")).strip(),
        "lu_name": p.get("lu_name", ""),
        "province": p.get("pv_tn", ""), "district": p.get("ap_tn", ""), "subdistrict": p.get("tb_tn", ""),
        "source": "gistda",
    }


def fetch_gistda(bbox):
    """ดึง hotspot จาก GISTDA ทั้ง 2 service → list dict"""
    out = []
    for svc, norm in [("hotspot_daily", _norm_daily), ("hotspot_npp_daily", _norm_npp)]:
        try:
            feats = _query_arcgis(svc, bbox)
            out.extend(norm(f["properties"]) for f in feats)
        except Exception as e:
            print(f"⚠️ GISTDA {svc} error: {e}")
    return out


# --------------------------------------------------------------------------
# NASA FIRMS (ถ้ามีคีย์ใน env)
# --------------------------------------------------------------------------
def fetch_firms(bbox, days=7, key=None):
    """ดึง active fire จาก FIRMS (VIIRS + MODIS) → list dict"""
    key = key or os.environ.get("FIRMS_KEY") or os.environ.get("FIRMS_MAP_KEY")
    if not key:
        return [], None
    out = []
    src = None
    for dataset in ("VIIRS_SNPP_NRT", "MODIS_NRT"):
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{dataset}"
            f"/{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}/{days}"
        )
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            if len(lines) < 2:
                continue
            header = lines[0].split(",")
            for line in lines[1:]:
                row = dict(zip(header, line.split(",")))
                out.append(_norm_firms(row))
            src = dataset
        except Exception as e:
            print(f"⚠️ FIRMS {dataset} error: {e}")
    return out, src


def _norm_firms(row):
    conf = row.get("confidence", "")
    try:
        conf = int(conf)
    except Exception:
        conf = {"l": 40, "n": 60, "h": 90}.get(str(conf).lower(), 50)
    try:
        frp = float(row.get("frp") or 0)
    except Exception:
        frp = 0.0
    return {
        "lat": float(row["latitude"]), "lon": float(row["longitude"]),
        "confidence": conf, "frp": round(frp, 3),
        "satellite": f"{row.get('satellite', '')} ({row.get('instrument', '')})".strip(),
        "datetime": f"{row.get('acq_date', '')} {row.get('acq_time', '')}".strip(),
        "lu_name": "", "province": "", "district": "", "subdistrict": "",
        "source": "firms",
    }


# --------------------------------------------------------------------------
# หลัก: รวมข้อมูล + กรอง + จัดอันดับ
# --------------------------------------------------------------------------
def _cache_get():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        if time.time() - data.get("ts", 0) < CACHE_TTL:
            return data["hotspots"]
    return None


def _cache_set(hotspots):
    os.makedirs(PROC_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as fh:
        json.dump({"ts": time.time(), "hotspots": hotspots}, fh, ensure_ascii=False)


def get_hotspots(bbox, use_cache=True, firms_days=7):
    """ดึง hotspot ทั้งหมด (GISTDA + FIRMS) ใน bbox พร้อม cache"""
    if use_cache:
        cached = _cache_get()
        if cached is not None:
            return cached, True
    hs = fetch_gistda(bbox)
    firms, _src = fetch_firms(bbox, days=firms_days)
    hs.extend(firms)
    _cache_set(hs)
    return hs, False


def rank(hotspots):
    """จัดอันดับ: score = FRP (ถ้ามี) ไม่งั้น confidence; เรียงจากมาก→น้อย"""
    for h in hotspots:
        h.setdefault("frp", 0)
        h["score"] = round(h.get("frp", 0) if h.get("frp", 0) > 0 else h.get("confidence", 0), 1)
    return sorted(hotspots, key=lambda h: h["score"], reverse=True)


def province_hotspots(province_name="บุรีรัมย์", use_cache=True):
    """ชุดข้อมูลครบสำหรับหน้าแผนที่: ขอบเขต + hotspot ในจังหวัด + อันดับ + สรุป"""
    feature, pname = find_province(province_name)
    if feature is None:
        return {"error": f"ไม่พบจังหวัด '{province_name}'"}

    bbox = province_bbox(feature)
    all_hs, from_cache = get_hotspots(bbox, use_cache=use_cache)

    inside = [h for h in all_hs if point_in_polygon(h["lat"], h["lon"], feature["geometry"])]
    inside = rank(inside)

    summary = {
        "province": pname,
        "count": len(inside),
        "from_cache": from_cache,
        "by_source": _tally(inside, "source"),
        "by_satellite": _tally(inside, "satellite"),
        "by_lu": _tally(inside, "lu_name"),
        "date_range": _date_range(inside),
        "top": inside[:10],
    }
    return {"boundary": feature, "hotspots": inside, "summary": summary}


def _tally(items, key):
    out = {}
    for it in items:
        k = it.get(key) or "(ไม่มีข้อมูล)"
        out[k] = out.get(k, 0) + 1
    return out


def _date_range(items):
    dates = sorted(h["datetime"][:10] for h in items if h.get("datetime"))
    return (dates[0], dates[-1]) if dates else ("", "")
