"""geo.greenchange — การเปลี่ยนแปลงพื้นที่สีเขียว / การขยายตัวของเมือง (Phase C)

เปรียบเทียบภาพดาวเทียม 2 ช่วงเวลา (ต้องเป็นฉากเดียวกัน / co-registered)
คำนวณ NDVI (ความเขียวขจี) และ NDBI (สิ่งก่อสร้าง) ทั้ง 2 ยุค ดูผลต่างตามพิกเซล
แล้วจัดกลุ่มเป็นคลาสการเปลี่ยนแปลง:

    0  ไม่เปลี่ยนแปลง          (unchanged, เทา)
    1  พื้นที่สีเขียวเพิ่มขึ้น    (greened, เขียว)         — ΔNDVI  > +th
    2  พื้นที่สีเขียวลดลง/เสื่อม  (green loss, แดง)       — ΔNDVI  < -th
    3  สิ่งก่อสร้างขยายตัว       (urban expansion, น้ำตาล) — ΔNDBI  > +th
    4  สิ่งก่อสร้างลดลง          (built-up decline, ครีม)  — ΔNDBI  < -th

ฟังก์ชันหลัก: analyze(path_t1, path_t2, ...) -> dict {png, stats, net_green_km2, ...}
"""
import os
import uuid

import numpy as np

from . import io
from . import indices
from . import visualize

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS = os.path.join(BASE_DIR, "outputs")

# คลาสการเปลี่ยนแปลง + สี (ตรงตามไลบรารีการวาด)
CHANGE_CLASSES = {
    0: {"th": "ไม่เปลี่ยนแปลง", "en": "unchanged", "color": "#9aa0a6"},
    1: {"th": "พื้นที่สีเขียวเพิ่มขึ้น", "en": "greened", "color": "#2e8b57"},
    2: {"th": "พื้นที่สีเขียวลดลง", "en": "green loss", "color": "#d62728"},
    3: {"th": "สิ่งก่อสร้างขยายตัว", "en": "urban expansion", "color": "#8b4513"},
    4: {"th": "สิ่งก่อสร้างลดลง", "en": "built-up decline", "color": "#d9c58c"},
}

# ค่า threshold (หน่วย reflectance 0–1) — ปรับเป็นพารามิเตอร์ได้
DEFAULT_NDVI_TH = 0.10
DEFAULT_NDBI_TH = 0.06
DEFAULT_NDBI_ABS = 0.0


def change_map(arr1, arr2, ndvi_th=DEFAULT_NDVI_TH, ndbi_th=DEFAULT_NDBI_TH,
               ndbi_abs=DEFAULT_NDBI_ABS):
    """จัดกลุ่มการเปลี่ยนแปลงรายพิกเซล (H,W) จาก 2 ภาพ (H,W,C).

    ลำดับแบนด์ทั้งสองภาพต้องตรงกัน (เช่น B02–B07 / R,G,B,NIR,SWIR)
    ใช้เกณฑ์ความเร็วลิ่ม (gate) ด้วยค่า NDBI สัมบูรณ์ เพื่อแยก "เมืองขยาย"
    ออกจาก "พื้นที่โล่ง/นา → กลับเขียว" (ซึ่ง ΔNDBI ลดเช่นกัน ไม่ใช่เมืองลด):
        เมืองขยาย : ΔNDBI > +th และ NDBI₂ สูง (เป็นตึกจริง)
        เมืองลด   : ΔNDBI < -th และ NDBI₁ สูง (เคยเป็นตึก)
        ที่เหลือ  : เรียงตาม ΔNDVI (เขียวเพิ่ม/ลด)
    """
    ndbi1 = indices.ndbi(arr1)
    ndbi2 = indices.ndbi(arr2)
    ndvi1 = indices.ndvi(arr1)
    ndvi2 = indices.ndvi(arr2)
    dndvi = ndvi2 - ndvi1
    dndbi = ndbi2 - ndbi1
    cls = np.zeros(arr1.shape[:2], dtype="int32")

    cls[(dndbi > ndbi_th) & (ndbi2 > ndbi_abs)] = 3          # สิ่งก่อสร้างขยายตัว
    cls[(dndbi < -ndbi_th) & (ndbi1 > ndbi_abs)] = 4         # สิ่งก่อสร้างลดลง
    rest = (cls == 0)
    cls[rest & (dndvi > ndvi_th)] = 1     # เขียวเพิ่ม
    cls[rest & (dndvi < -ndvi_th)] = 2    # เขียวลด
    return cls, dndvi, dndbi


def _stats(cls, classes, pixel_area_m2=None):
    total = cls.size
    rows = []
    for k, meta in classes.items():
        n = int((cls == int(k)).sum())
        area_m2 = n * pixel_area_m2 if pixel_area_m2 else None
        row = dict(
            class_id=int(k),
            label_th=meta["th"], label_en=meta["en"], color=meta["color"],
            pixels=n, pct=round(100.0 * n / total, 3),
        )
        if area_m2 is not None:
            row.update(
                area_m2=round(area_m2, 2),
                area_ha=round(area_m2 / 10000.0, 3),
                area_km2=round(area_m2 / 1e6, 5),
            )
        rows.append(row)
    return rows


def _net_km2(stats, marker, pixel_area_m2):
    """ผลรวมสุทธิ (km²) ของกลุ่มที่ยืนยันจาก marker."""
    if not pixel_area_m2:
        return None
    ha = (pixel_area_m2 / 1e4)
    gain = sum(s["pixels"] for s in stats if s["class_id"] in marker["gain"])
    loss = sum(s["pixels"] for s in stats if s["class_id"] in marker["loss"])
    return dict(
        net_ha=round((gain - loss) * ha, 3),
        gain_ha=round(gain * ha, 3),
        loss_ha=round(loss * ha, 3),
    )


def analyze(path_t1, path_t2, out_id=None, ndvi_th=DEFAULT_NDVI_TH, ndbi_th=DEFAULT_NDBI_TH,
            ndbi_abs=DEFAULT_NDBI_ABS):
    """เปรียบเทียบ 2 ภาพ → ออก diff map PNG + สถิติพื้นที่ + ผลต่างสุทธิ.

    คืน dict {class_map, classes, png, stats, net_green, net_built, meta}.
    ภาพทั้งสองต้องมีขนาดเท่ากัน (ฉากเดียวกัน 2 ช่วงเวลา)
    """
    arr1, meta1 = io.read_tiff(path_t1)
    arr2, meta2 = io.read_tiff(path_t2)

    if arr1.shape[:2] != arr2.shape[:2]:
        raise ValueError(
            f"ภาพทั้งสองฉากต้องมีขนาดเท่ากัน จริง: t1={arr1.shape[:2]} t2={arr2.shape[:2]} "
            "(ใช้ฉากเดียวกัน ช่วงเวลาต่างกัน)"
        )
    a1 = indices.to_reflectance(arr1)
    a2 = indices.to_reflectance(arr2)

    cls, _, _ = change_map(a1, a2, ndvi_th, ndbi_th, ndbi_abs)
    os.makedirs(OUTPUTS, exist_ok=True)
    fid = out_id or uuid.uuid4().hex[:8]
    png = os.path.join(OUTPUTS, f"{fid}_greendiff.png")
    visualize.render_class_png(cls, CHANGE_CLASSES, png)

    area = io.pixel_area_m2(meta1)
    stats = _stats(cls, CHANGE_CLASSES, area)
    net_green = _net_km2(stats, {"gain": [1], "loss": [2]}, area)
    net_built = _net_km2(stats, {"gain": [3], "loss": [4]}, area)

    return dict(
        class_map=cls,
        classes=CHANGE_CLASSES,
        png="/outputs/" + os.path.basename(png),
        stats=stats,
        net_green=net_green,
        net_built=net_built,
        meta=meta1,
        thresholds={"ndvi": ndvi_th, "ndbi": ndbi_th, "ndbi_abs": ndbi_abs},
        pixel_area_m2=area,
    )