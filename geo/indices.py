"""geo.indices — ดัชนีสเปกตรัม + ตัวจำแนก land cover แบบ baseline

เป็นตัวสำรอง/ตัวตรวจสอบ (sanity check) รันบน CPU ได้ทันที ไม่ต้องเทรน
ใช้ NDVI / NDWI / NDBI จำแนก 4 คลาส: น้ำ, พืชพรรณ, พื้นโล่ง, สิ่งก่อสร้าง
"""
import numpy as np


def to_reflectance(arr):
    """ปรับสเกลให้เป็น reflectance 0–1 (HLS/uint16 มักเป็น 0–10000)."""
    if arr.max() > 2.0:
        return arr / 10000.0
    return arr


def _bands(arr):
    """แยกแบนด์ตามจำนวนช่องที่พบ (สมมุติลำดับมาตรฐาน)."""
    C = arr.shape[2]
    if C >= 6:  # HLS: Blue, Green, Red, NIR, SWIR1, SWIR2
        return dict(
            blue=arr[..., 0], green=arr[..., 1], red=arr[..., 2],
            nir=arr[..., 3], swir=arr[..., 4],
        )
    if C >= 4:  # 4 แบนด์: R, G, B, NIR
        return dict(
            red=arr[..., 0], green=arr[..., 1], blue=arr[..., 2],
            nir=arr[..., 3], swir=arr[..., 3],
        )
    # 3 แบนด์ RGB — ไม่มี NIR จึงจำกัดความแม่นยำ
    return dict(
        red=arr[..., 0], green=arr[..., 1], blue=arr[..., 2],
        nir=arr[..., 2], swir=arr[..., 2],
    )


def _norm(a, b):
    d = a + b
    return np.where(d == 0, 0.0, (a - b) / np.where(d == 0, 1.0, d))


def ndvi(arr):
    b = _bands(arr)
    return _norm(b["nir"], b["red"])


def ndwi(arr):
    b = _bands(arr)
    return _norm(b["green"], b["nir"])


def ndbi(arr):
    b = _bands(arr)
    return _norm(b["swir"], b["nir"])


BASELINE_CLASSES = {
    0: {"th": "น้ำ", "en": "water", "color": "#1f77b4"},
    1: {"th": "พืชพรรณ", "en": "vegetation", "color": "#2ca02c"},
    2: {"th": "พื้นโล่ง/ดิน", "en": "bare soil", "color": "#d9b38c"},
    3: {"th": "สิ่งก่อสร้าง", "en": "built-up", "color": "#d62728"},
}


def baseline_classify(arr):
    """จำแนก land cover 4 คลาสจากดัชนีสเปกตรัม (ไม่มีโมเดล)."""
    arr = to_reflectance(arr)
    w = ndwi(arr)
    v = ndvi(arr)
    u = ndbi(arr)
    cls = np.zeros(arr.shape[:2], dtype="int32")
    water = w > 0.0
    veg = (~water) & (v > 0.2)
    built = (~water) & (~veg) & (u > 0.0)
    cls[water] = 0
    cls[veg] = 1
    cls[built] = 3
    cls[~water & ~veg & ~built] = 2
    return cls
