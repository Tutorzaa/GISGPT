"""agent.tools — เครื่องมือ (tools) ที่ agent เรียกใช้

แต่ละฟังก์ชัน: func(ctx, **args) -> dict
คีย์ที่ใช้ได้ (Ticket 03):
- text       : ข้อความตอบกลับ (str)
- artifacts  : ภาพ/ไฟล์/ลิงก์ (list)        [เดิม]
- data       : ข้อมูลดิบ เช่น classes       [เดิม]
- data_points: จุดบนแผนที่ (list)           [ใหม่]
- layers     : ชื่อชั้นภาพที่อยากให้ show    [ใหม่]
- chart      : ข้อมูลกราฟ correlation       [ใหม่]

ctx = หน่วยความจำของ session (ดู agent/memory.py)
"""
import json
import os
import uuid

from geo import hotspots as hotspots_mod
from geo import io as geo_io
from geo import pipeline
from geo import greenchange as gc
from analysis import correlation as corr_mod
from datasources import gistda, nasa_power, open_meteo
from geo.indices import BASELINE_CLASSES
from .registry import Tool

OUTPUTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")


def _no_image():
    return {"text": "ยังไม่มีภาพ — ลากไฟล์ GeoTIFF (Sentinel-2/Landsat) มาวางในช่องแชทเพื่ออัปโหลดก่อนนะ"}


def t_list_images(ctx, **kw):
    cur = ctx.get("current")
    if not cur:
        return _no_image()
    return {
        "text": (
            f"ภาพปัจจุบัน: **{cur['name']}**\n"
            f"- {cur['bands']} แบนด์ · {cur['width']}×{cur['height']} px\n"
            f"- CRS: {cur['crs']} · dtype: {cur['dtype']}"
        )
    }


def t_classify(ctx, **kw):
    cur = ctx.get("current")
    if not cur:
        return _no_image()
    res = pipeline.run_classification(cur["path"], cur.get("file_id"))
    ctx["last"] = res

    mode_th = "Prithvi (ONNX)" if res["mode"] == "prithvi" else "baseline (NDVI/NDWI/NDBI)"
    lines = [f"จำแนก land cover เสร็จแล้ว (โมเดล: {mode_th})\nเปอร์เซ็นต์พื้นที่แต่ละคลาส:"]
    for s in res["stats"]:
        lines.append(f"- {s['label_th']} ({s['label_en']}): {s['pct']}%")
    return {
        "text": "\n".join(lines),
        "artifacts": [
            {"type": "image", "url": res["preview"], "caption": "ภาพต้นฉบับ (RGB preview)"},
            {"type": "image", "url": res["png"], "caption": "ผลจำแนก land cover"},
        ],
        "data": res,
    }


def t_index(ctx, which="ndvi", **kw):
    cur = ctx.get("current")
    if not cur:
        return _no_image()
    res = pipeline.run_index(cur["path"], which, cur.get("file_id"))
    th = {"ndvi": "ดัชนีความเขียวขจี", "ndwi": "ดัชนีน้ำ", "ndbi": "ดัชนีสิ่งก่อสร้าง"}[which]
    return {
        "text": f"คำนวณ **{which.upper()}** ({th}) เสร็จแล้ว — ค่าสูง (เขียว/แดงเข้ม) = มีมาก, ค่าต่ำ = มีน้อย",
        "artifacts": [{"type": "image", "url": res["url"], "caption": f"{which.upper()} index map"}],
        "data": res,
    }


def t_stats(ctx, **kw):
    last = ctx.get("last")
    if not last:  # ยังไม่เคยจำแนก → ทำ classification ให้ก่อน
        return t_classify(ctx)
    lines = ["สถิติพื้นที่รายคลาส:"]
    for s in last["stats"]:
        if "area_ha" in s:
            lines.append(
                f"- **{s['label_th']}**: {s['pct']}% · {s['area_ha']:,.1f} เฮกตาร์ "
                f"({s['area_km2']:,.2f} ตร.กม.)"
            )
        else:
            lines.append(f"- **{s['label_th']}**: {s['pct']}% ({s['pixels']:,} พิกเซล)")
    return {"text": "\n".join(lines), "data": last}


def t_explain(ctx, **kw):
    last = ctx.get("last")
    classes = (last or {}).get("classes") or BASELINE_CLASSES
    lines = ["คลาส land cover ในผลลัพธ์:"]
    for k, v in classes.items():
        lines.append(f"- **{v['th']}** ({v['en']}) — สี {v['color']}")
    lines.append("\n💡 ถามต่อได้ เช่น 'พื้นที่ป่าเท่าไหร่' หรือ 'คำนวณ NDVI'")
    return {"text": "\n".join(lines), "data": last}


def t_export(ctx, fmt="geotiff", **kw):
    cur = ctx.get("current")
    last = ctx.get("last")
    if not cur or not last:
        return {"text": "ต้องอัปโหลดภาพและจำแนก land cover ก่อน ถึงจะส่งออกได้"}
    os.makedirs(OUTPUTS, exist_ok=True)
    out = os.path.join(OUTPUTS, f"{(cur.get('file_id') or 'export')}_{uuid.uuid4().hex[:4]}_landcover.tif")
    geo_io.write_tiff(out, last["class_map"][..., None], last["meta"])
    return {
        "text": f"ส่งออกผลลัพธ์เป็น GeoTIFF เรียบร้อย (แบนด์เดียว = class id)",
        "artifacts": [{"type": "download", "url": "/outputs/" + os.path.basename(out), "caption": "landcover GeoTIFF"}],
    }


def t_help(ctx, **kw):
    lines = [
        "Hello! I'm GISGPT — Geospatial Foundation Model Agent 🌍",
        "",
        "Natural-language examples (Thai & English both work):",
        "- 'Show hotspots in Buriram' / 'จุดไฟในบุรีรัมย์' → satellite hotspots on map",
        "- 'Show temperature in this area' / 'อุณหภูมิพื้นที่นี้' → weather data points",
        "- 'Are hotspots correlated with temperature?' / 'จุดไฟกับอุณหภูมิสัมพันธ์กันไหม' → correlation chart",
        "- 'Classify land cover' / 'จำแนก land cover' → pixel land-cover layer",
        "- 'Compare 2 time periods' / 'เปรียบเทียบ 2 ช่วง' → change detection",
        "",
        "For image analysis you can also upload a GeoTIFF (Sentinel-2/Landsat).",
    ]
    return {"text": "\n".join(lines)}


def t_fire_hotspots(ctx, province="บุรีรัมย์", **kw):
    """จุดความร้อน (การเผาไหม้) ในจังหวัด + จัดอันดับ — ลิงก์ไปหน้าแผนที่"""
    data = hotspots_mod.province_hotspots(province)
    if "error" in data:
        return {"text": data["error"]}
    s = data["summary"]
    lines = [
        f"🔥 จุดความร้อนในจังหวัด **{s['province']}**: {s['count']} จุด",
        f"ช่วงวันที่: {s['date_range'][0]} → {s['date_range'][1]}",
        f"ดาวเทียม: {json.dumps(s['by_satellite'], ensure_ascii=False)}",
        "", "อันดับ Top 5 (score = ความรุนแรง):",
    ]
    for t in s["top"][:5]:
        lines.append(
            f"  #{t['score']} ({t['lat']:.4f}, {t['lon']:.4f}) {t['datetime']} {t['satellite'] or ''}"
        )
    return {
        "text": "\n".join(lines),
        "artifacts": [{"type": "link", "url": "/hotspots", "caption": "เปิดแผนที่ hotspot"}],
        "data": data,
    }


def _pick_two_images(ctx):
    """คืน 2 ภาพล่าสุด (t1 = เก่า, t2 = ใหม่) จากภาพที่อัปโหลดใน session."""
    imgs = ctx.get("images") or []
    if len(imgs) < 2:
        return None
    t1, t2 = imgs[-2], imgs[-1]
    if t1.get("path") == t2.get("path"):
        return None
    return t1, t2


# ---------------------------------------------------------------------------
# Ticket 14–16: tools ที่คืน data_points / layers / chart (ผูกกับ /api/query)
# ---------------------------------------------------------------------------
DEFAULT_BBOX = [102.6, 14.4, 103.4, 15.4]  # บุรีรัมย์ (ถ้า query ไม่ระบุ bbox)


def _area(ctx):
    q = ctx.get("query") or {}
    b = q.get("bbox")
    if b and len(b) == 4:
        try:
            return [float(x) for x in b]
        except (TypeError, ValueError):
            pass
    return DEFAULT_BBOX


def _pts(rows):
    return [{"lat": r.lat, "lon": r.lon, "value": r.value, "metric": r.metric}
            for r in rows]


def t_met_query(ctx, metric="t2m", **kw):
    """Weather (NASA POWER temperature) over area → data_points + layer."""
    q = ctx.get("query") or {}
    bbox = _area(ctx)
    start = q.get("start", "2023-04-05")
    rows = nasa_power.grid(bbox, start, start, params=("T2M",), step_km=25.0)
    if not rows:
        return {"text": "No temperature data in this area."}
    avg = sum(r.value for r in rows) / len(rows)
    return {
        "text": f"🌡️ Temperature (NASA POWER): {len(rows)} points in selected area — "
                f"avg {avg:.1f} °C",
        "data_points": _pts(rows),
        "layers": ["power_t2m"],
    }


def t_satellite_query(ctx, metric="hotspot", **kw):
    """Satellite hotspots (GISTDA) → data_points + layer."""
    bbox = _area(ctx)
    rows = gistda.hotspot_rows(bbox)
    if not rows:
        return {"text": "No hotspots in this area."}
    top = sorted(rows, key=lambda r: r.value, reverse=True)[:3]
    lines = [f"🔥 Hotspots (GISTDA): {len(rows)} points — highest intensity:"]
    lines += [f"  · ({r.lat:.3f}, {r.lon:.3f}) score {r.value}" for r in top]
    return {
        "text": "\n".join(lines),
        "data_points": _pts(rows),
        "layers": ["hotspot"],
    }


def t_correlation(ctx, metric_a="hotspot_conf", metric_b="power_t2m", **kw):
    """Prove the relationship between 2 metrics (satellite ↔ weather) → chart + text."""
    from api.correlation_api import _rows

    bbox = _area(ctx)
    q = ctx.get("query") or {}
    try:
        a = _rows(metric_a, bbox, q)
        b = _rows(metric_b, bbox, q)
    except ValueError as e:
        return {"text": f"⚠️ {e}"}
    res = corr_mod.cross_sectional(a, b, radius_km=float(q.get("radius_km", 60)),
                                   metric_a=metric_a, metric_b=metric_b)
    if res.get("note"):
        return {"text": res["note"], "chart": res}
    verdict = "significant" if res["p"] < 0.05 else "not clearly significant"
    return {
        "text": (f"📊 {metric_a} ↔ {metric_b}: r={res['r']}, p={res['p']} (n={res['n']}) "
                 f"→ {verdict} (note: correlation ≠ causation)"),
        "chart": res,
        "layers": ["hotspot"],
    }


def t_green_change(ctx, **kw):
    """Phase C — เปรียบเทียบการเปลี่ยนแปลงพื้นที่สีเขียว/เมือง จากภาพ 2 ช่วงเวลา"""
    pair = _pick_two_images(ctx)
    if pair is None:
        return {
            "text": "ต้องอัปโหลด **ภาพดาวเทียม 2 ช่วงเวลา** (ฉากเดียวกัน) ก่อน ถึงจะเปรียบเทียบได้\n"
                    "เช่น ภาพ มี.ค. กับ เม.ย. — อัปโหลดภาพแรก แล้วอัปโหลดภาพที่สอง แล้วถาม 'เปรียบเทียบ'"
        }
    t1, t2 = pair
    base_id = f"{t1.get('file_id') or 'x'}__{t2.get('file_id') or 'x'}"
    try:
        res = gc.analyze(t1["path"], t2["path"], out_id=base_id)
    except ValueError as e:
        return {"text": f"⚠️ {e}"}

    lines = [
        f"🟢↔🟤 เปรียบเทียบ {t1['name']} (t1) กับ {t2['name']} (t2):",
        "",
    ]
    for s in res["stats"]:
        if "area_ha" in s:
            lines.append(
                f"  - **{s['label_th']}**: {s['pct']}% · {s['area_ha']:,.1f} เฮกตาร์ "
                f"({s['area_km2']} ตร.กม.)"
            )
        else:
            lines.append(f"  - **{s['label_th']}**: {s['pct']}% ({s['pixels']:,} พิกเซล)")
    ng, nb = res["net_green"], res["net_built"]
    if ng and nb:
        lines += [
            "",
            f"📉 สีเขียว **สุทธิ**: {ng['net_ha']:+,.1f} เฮกตาร์ "
            f"(เพิ่ม {ng['gain_ha']:,.1f} / ลด {ng['loss_ha']:,.1f})",
            f"🏙️ สิ่งก่อสร้าง **สุทธิ**: {nb['net_ha']:+,.1f} เฮกตาร์ "
            f"(เพิ่ม {nb['gain_ha']:,.1f} / ลด {nb['loss_ha']:,.1f})",
            f"threshold: ΔNDVI>{res['thresholds']['ndvi']:.2f}, ΔNDBI>{res['thresholds']['ndbi']:.2f}",
        ]
    ctx["last"] = res
    return {
        "text": "\n".join(lines),
        "artifacts": [{
            "type": "image", "url": res["png"],
            "caption": "แผนที่การเปลี่ยนแปลง (เขียว=เพิ่ม, แดง=ลด, น้ำตาล=เมืองขยาย)",
        }],
        "data": res,
    }


def t_elevation(ctx, **kw):
    """Mountain peaks (SRTM elevation) in the selected area, ranked."""
    from analysis.peaks import find_peaks
    from datasources.terrain import elevation as elev

    bbox = _area(ctx)
    step = float((ctx.get("query") or {}).get("step_km", 20))
    rows = elev.grid(bbox, step_km=step)
    if not rows:
        return {"text": "No elevation data in this area."}
    peaks = find_peaks(rows, min_elev=400.0, top_n=8)
    if not peaks:
        return {"text": "No significant peaks found in this area."}
    lines = [f"🏔️ Mountain peaks in area (top {len(peaks)}):"]
    lines += [f"  #{i+1} · ({p['lat']:.3f}, {p['lon']:.3f}) — {p['elev']:.0f} m"
              for i, p in enumerate(peaks)]
    return {
        "text": "\n".join(lines),
        "data_points": [{"lat": p["lat"], "lon": p["lon"], "value": p["elev"],
                         "metric": "elevation_m"} for p in peaks],
        "layers": ["elevation"],
    }


def register_tools(registry):
    registry.register(Tool("classify", "จำแนก land cover จากภาพดาวเทียม", [], t_classify, "analysis"))
    registry.register(Tool("index", "คำนวณดัชนีสเปกตรัม (which=ndvi/ndwi/ndbi)", ["which"], t_index, "analysis"))
    registry.register(Tool("stats", "สถิติพื้นที่รายคลาส", [], t_stats, "analysis"))
    registry.register(Tool("explain", "อธิบายคลาส land cover", [], t_explain, "info"))
    registry.register(Tool("list_images", "แสดงภาพที่อัปโหลด", [], t_list_images, "info"))
    registry.register(Tool("export", "ส่งออกผลลัพธ์เป็น GeoTIFF", ["fmt"], t_export, "io"))
    registry.register(Tool("fire_hotspots", "จุดความร้อน/การเผาไหม้ในจังหวัด (province=ชื่อจังหวัด)", ["province"], t_fire_hotspots, "analysis"))
    registry.register(Tool("green_change", "เปรียบเทียบการเปลี่ยนแปลงพื้นที่สีเขียว/เมือง 2 ช่วงเวลา", [], t_green_change, "analysis"))
    registry.register(Tool("met_query", "สภาพอากาศ/อุณหภูมิจาก NASA POWER", ["metric"], t_met_query, "analysis"))
    registry.register(Tool("satellite_query", "จุดความร้อนจากดาวเทียม (GISTDA)", ["metric"], t_satellite_query, "analysis"))
    registry.register(Tool("correlation", "พิสูจน์ความสัมพันธ์ 2 metric (ดาวเทียม↔สภาพอากาศ)", ["metric_a", "metric_b"], t_correlation, "analysis"))
    registry.register(Tool("elevation_query", "อันดับยอดเขาจากความสูง (SRTM)", [], t_elevation, "analysis"))
    registry.register(Tool("help", "แสดงความสามารถของ agent", [], t_help, "info"))
