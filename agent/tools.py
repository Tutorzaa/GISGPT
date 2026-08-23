"""agent.tools — เครื่องมือ (tools) ที่ agent เรียกใช้

แต่ละฟังก์ชัน: func(ctx, **args) -> dict {text, artifacts, data}
ctx = หน่วยความจำของ session (ดู agent/memory.py)
"""
import json
import os
import uuid

from geo import hotspots as hotspots_mod
from geo import io as geo_io
from geo import pipeline
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
        "สวัสดี! ผม GISGPT — agent ด้าน GIS 🌍",
        "",
        "ลองสั่งงานแบบนี้ได้เลย:",
        "- อัปโหลดภาพดาวเทียม (GeoTIFF) แล้วถาม **'จำแนก land cover'**",
        "- **'คำนวณ NDVI' / 'NDWI' / 'NDBI'** — ดัชนีสเปกตรัม",
        "- **'สถิติพื้นที่'** — พื้นที่แต่ละคลาส (เฮกตาร์/ตร.กม.)",
        "- **'อธิบายคลาส'** — ความหมายของแต่ละประเภท",
        "- **'export'** — ส่งออกผลลัพธ์เป็น GeoTIFF",
        "",
        "ตอนนี้รันด้วย baseline (NDVI/NDWI/NDBI) — เมื่อเทรน Prithvi เสร็จจาก Colab จะสลับใช้โมเดล GFM อัตโนมัติ",
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


def register_tools(registry):
    registry.register(Tool("classify", "จำแนก land cover จากภาพดาวเทียม", [], t_classify, "analysis"))
    registry.register(Tool("index", "คำนวณดัชนีสเปกตรัม (which=ndvi/ndwi/ndbi)", ["which"], t_index, "analysis"))
    registry.register(Tool("stats", "สถิติพื้นที่รายคลาส", [], t_stats, "analysis"))
    registry.register(Tool("explain", "อธิบายคลาส land cover", [], t_explain, "info"))
    registry.register(Tool("list_images", "แสดงภาพที่อัปโหลด", [], t_list_images, "info"))
    registry.register(Tool("export", "ส่งออกผลลัพธ์เป็น GeoTIFF", ["fmt"], t_export, "io"))
    registry.register(Tool("fire_hotspots", "จุดความร้อน/การเผาไหม้ในจังหวัด (province=ชื่อจังหวัด)", ["province"], t_fire_hotspots, "analysis"))
    registry.register(Tool("help", "แสดงความสามารถของ agent", [], t_help, "info"))
