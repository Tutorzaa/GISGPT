"""สร้างภาพ GeoTIFF จำลอง (6 แบนด์ HLS 0–10000) สำหรับเทสต์ pipeline โดยไม่ต้องโหลดข้อมูลจริง

รัน:  python scripts/make_test_tiff.py
เขียนผลที่: data/sample/test.tif  (512×512, CRS EPSG:32648, 30 ม./พิกเซล)
ภูมิประเทศจำลอง: เมือง / พื้นโล่ง / น้ำ / พืชพรรณ + แม่น้ำทแยง
"""
import os
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin

# คอนโซล Windows (cp1252) ไม่อ่านภาษาไทย → บังคับ UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

H = W = 512
# แบนด์ลำดับ HLS: Blue, Green, Red, NIR, SWIR1, SWIR2 (reflectance 0–1)
SIG = {
    "water":  np.array([0.08, 0.10, 0.04, 0.02, 0.01, 0.01]),
    "veg":    np.array([0.05, 0.12, 0.05, 0.50, 0.15, 0.10]),
    "bare":   np.array([0.10, 0.14, 0.20, 0.25, 0.32, 0.28]),
    "urban":  np.array([0.20, 0.22, 0.28, 0.22, 0.40, 0.36]),
}


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "test.tif")

    arr = np.zeros((H, W, 6), dtype="float32")
    arr[:] = SIG["veg"]
    arr[: H // 2, : W // 2] = SIG["urban"]   # มุมซ้ายบน = เมือง
    arr[: H // 2, W // 2:] = SIG["bare"]     # มุมขวาบน = พื้นโล่ง
    arr[H // 2:, W // 2:] = SIG["veg"]       # มุมขวาล่าง = พืชพรรณ
    arr[H // 2:, : W // 2] = SIG["water"]    # มุมซ้ายล่าง = น้ำ

    # แม่น้ำทแยงมุม
    yy, xx = np.mgrid[0:H, 0:W]
    arr[np.abs(xx - yy) < 14] = SIG["water"]

    # noise เบา ๆ ให้สมจริงขึ้น
    rng = np.random.default_rng(42)
    arr *= rng.uniform(0.92, 1.08, arr.shape)

    data = np.clip(arr * 10000, 0, 10000).astype("uint16")  # สเกล HLS
    transform = from_origin(600000, 1660000, 30, 30)  # UTM 48N (ประมาณเขตบุรีรัมย์)

    with rasterio.open(
        out, "w", driver="GTiff", height=H, width=W, count=6,
        dtype="uint16", crs="EPSG:32648", transform=transform,
    ) as dst:
        dst.write(np.moveaxis(data, -1, 0))

    print(f"สร้างข้อมูลทดสอบแล้ว: {out}")
    print(f"ขนาด {W}×{H} px · 6 แบนด์ · CRS EPSG:32648 · พิกเซลละ 30×30 ม. (900 ตร.ม.)")


if __name__ == "__main__":
    main()
