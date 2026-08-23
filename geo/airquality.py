"""geo/airquality.py — ดึงข้อมูลคุณภาพอากาศ (PM2.5/PM10) + อนุกรม hotspot สำหรับ Phase B

แหล่งข้อมูล:
- GISTDA AirQuality_daily  — สถานี 70 แห่ง (ตัวอย่าง 2020-08-29) — เปิดสาธารณะ ใช้ได้ทันที
- OpenAQ v3                — สถานีจริง ย้อนหลัง (ต้องคีย์ OPENAQ_KEY ใน env)
- CAMS EAC4 reanalysis     — PM2.5 รายวันที่ทุกพิกัด (ต้องคีย์ ADS → .cdsapirc)
- NASA FIRMS archive       — hotspot รายวันย้อนหลัง (ต้อง FIRMS_KEY)

การวิเคราะห์: ดู geo/analysis.py (nearest_stations, station_hotspot_stats,
cross_sectional_correlation, time_series_correlation)
"""
import datetime
import os
import time

import requests

from . import analysis
from . import hotspots as hs

AQ_BASE = "https://gistdaportal.gistda.or.th/data/rest/services/FR_Fire/AirQuality_daily/MapServer/0/query"
AQ_CACHE = os.path.join(hs.PROC_DIR, "airquality_cache.json")


def _to_num(v):
    try:
        return float(v)
    except Exception:
        return None


# --------------------------------------------------------------------------
# GISTDA AirQuality_daily (สาธารณะ — ใช้ได้ทันที)
# --------------------------------------------------------------------------
def fetch_gistda_aq():
    """ดึง 70 สถานี (ตัวอย่าง 2020-08-29) → list dict"""
    if os.path.exists(AQ_CACHE):
        with open(AQ_CACHE, encoding="utf-8") as fh:
            import json

            return json.load(fh)

    r = requests.get(
        AQ_BASE + "?where=1%3D1&outFields=*&f=geojson", timeout=30
    )
    r.raise_for_status()
    stations = []
    for f in r.json().get("features", []):
        p = f["properties"]
        stations.append({
            "st_id": p.get("st_id", ""),
            "st_name": p.get("st_name", ""),
            "lat": float(p.get("latitude", 0)),
            "lon": float(p.get("longitude", 0)),
            "pm25": _to_num(p.get("pm25")),
            "pm10": _to_num(p.get("pm10")),
            "datetime": _epoch(p.get("datetime")),
            "province": p.get("pv_tn", ""),
            "district": p.get("ap_tn", ""),
        })
    os.makedirs(hs.PROC_DIR, exist_ok=True)
    import json

    with open(AQ_CACHE, "w", encoding="utf-8") as fh:
        json.dump(stations, fh, ensure_ascii=False)
    return stations


def _epoch(ms):
    try:
        return time.strftime("%Y-%m-%d", time.localtime(int(ms) / 1000))
    except Exception:
        return ""


# --------------------------------------------------------------------------
# NASA FIRMS archive (ต้อง FIRMS_KEY) — hotspot รายวันย้อนหลัง
# --------------------------------------------------------------------------
def fetch_firms_archive(bbox, date, dataset="VIIRS_SNPP_SP", day_range=1):
    """hotspot ย้อนหลัง (Standard Processing) — คืน (list dict, dataset)

    format ปัจจุบัน: /area/csv/{key}/{dataset}/{bbox}/{day_range}/{YYYY-MM-DD}
    ข้อมูลเก่าใช้ *_SP (NRT มีแค่ ~10 วันหลัง)
    """
    key = os.environ.get("FIRMS_KEY") or os.environ.get("FIRMS_MAP_KEY")
    if not key:
        return [], "no FIRMS_KEY"
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{dataset}"
        f"/{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}/{day_range}/{date}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    if len(lines) < 2:
        return [], "no data"
    header = lines[0].split(",")
    out = []
    for line in lines[1:]:
        row = dict(zip(header, line.split(",")))
        conf = row.get("confidence", "")
        try:
            conf = int(conf)
        except Exception:
            conf = {"l": 40, "n": 60, "h": 90}.get(str(conf).lower(), 50)
        try:
            frp = float(row.get("frp") or 0)
        except Exception:
            frp = 0.0
        out.append({
            "lat": float(row["latitude"]), "lon": float(row["longitude"]),
            "confidence": conf, "frp": round(frp, 3),
            "satellite": row.get("satellite", ""),
            "datetime": f"{row.get('acq_date', '')} {row.get('acq_time', '')}".strip(),
            "source": "firms-" + dataset.lower(),
        })
    return out, dataset


# --------------------------------------------------------------------------
# OpenAQ v3 (ต้อง OPENAQ_KEY) — PM2.5 สถานีจริงย้อนหลัง
# --------------------------------------------------------------------------
def fetch_openaq_pm25(location_id, start, end, parameter_id=2):
    """PM2.5 รายชั่วโมง/วัน ของ location (v3) — คืน list {datetime, pm25}

    location_id: หาจาก /v3/locations?name=... หรือใช้ st_id ที่รู้อยู่แล้ว
    """
    key = os.environ.get("OPENAQ_KEY")
    if not key:
        return [], "no OPENAQ_KEY"
    url = (
        f"https://api.openaq.org/v3/locations/{location_id}/sensors/{parameter_id}/measurements"
        f"?start={start}&end={end}&limit=500&sort=asc"
    )
    r = requests.get(url, headers={"X-API-Key": key}, timeout=30)
    r.raise_for_status()
    out = []
    for m in r.json().get("results", []):
        out.append({
            "datetime": m.get("datetime"),
            "pm25": _to_num(m.get("value")),
        })
    return out, "openaq"


# --------------------------------------------------------------------------
# CAMS EAC4 reanalysis (ต้อง cdsapi + .cdsapirc) — PM2.5 รายวันที่ทุกพิกัด
# --------------------------------------------------------------------------
def fetch_cams_daily_pm25(lat, lon, start_date, end_date):
    """PM2.5 รายวันที่จุดพิกัด (EAC4 0.75°) — คืน list {date, pm25} µg/m³

    ต้องการ: pip install cdsapi + ตั้งคีย์ใน ~/.cdsapirc (จาก ads.atmosphere.copernicus.eu)
    """
    try:
        import cdsapi
        import xarray as xr
    except Exception as e:
        return [], f"need cdsapi+xarray: {e}"

    c = cdsapi.Client()
    os.makedirs(hs.PROC_DIR, exist_ok=True)
    target = os.path.join(hs.PROC_DIR, "cams_eac4_pm25.nc")
    c.retrieve(
        "cams-global-reanalysis-eac4",
        {
            "variable": "particulate_matter_2.5um",  # ชื่อจริงใน ADS (ตรวจจาก form.json)
            "date": f"{start_date}/{end_date}",
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": f"{lat + 1}/{lon - 1}/{lat - 1}/{lon + 1}",  # north/west/south/east
            "data_format": "netcdf",
        },
        target,
    )
    ds = xr.open_dataset(target)
    # หาชื่อตัวแปรใน netCDF (อาจเป็น pm2p5 หรือชื่ออื่น)
    for cand in ("pm2p5", "particulate_matter_2.5um", "pm2.5"):
        if cand in ds:
            v = ds[cand]
            break
    else:
        v = ds[list(ds.data_vars)[0]]
    try:
        v = v.sel(latitude=lat, longitude=lon, method="nearest")
    except Exception:
        pass
    time_dim = "valid_time" if "valid_time" in v.dims else "time"  # ECMWF ใช้ valid_time
    daily = v.resample({time_dim: "1D"}).mean(dim=time_dim)
    # หน่วย kg/m³ → µg/m³ (คูณ 1e9) แล้วปัดเป็น 1 ทศนิยม
    out = [
        {"date": str(t)[:10], "pm25": round(float(daily.sel({time_dim: t})) * 1e9, 1)}
        for t in daily[time_dim].values
    ]
    return out, "cams-eac4"


# --------------------------------------------------------------------------
# รวมชุดข้อมูลรายวันสำหรับ time-series correlation
# --------------------------------------------------------------------------
def daily_series(hotspots):
    """จาก list hotspot → {date: {count, sum_frp, sum_score}}"""
    out = {}
    for h in hotspots:
        d = (h.get("datetime") or "")[:10]
        if not d:
            continue
        row = out.setdefault(d, {"count": 0, "sum_frp": 0.0, "sum_score": 0.0})
        row["count"] += 1
        row["sum_frp"] += h.get("frp", 0)
        row["sum_score"] += h.get("score", h.get("confidence", 0))
    return out
