"""สร้างภาพ GeoTIFF จำลอง 2 ช่วงเวลา (t1/t2) สำหรับเทสต์ Phase C — การเปลี่ยนแปลง

ฉาก 256×256, 6 แบนด์ ลำดับเดียวกับ pipeline (Blue,Green,Red,NIR,SWIR1,SWIR2),
สเกล 0–10000 (to_reflectance หาร 10000). มี:
  - พื้นที่เกษตร/ป่า (NDVI สูง)   ส่วนใหญ่
  - ตึกในเมือง (NDBI สูง)        มุมบนซ้าย
  - แม่น้ำ (NDWI สูง)            แถบล่าง
  - ดินโล่งแถบขวาบน

ระหว่าง t1 → t2 (สิ่งที่เราอยากให้ engine จับได้ — แต่ละโซนไม่ทับกัน):
  [A] ดินโล่ง → เขียวเพิ่มขึ้น    (NDVI ↑)  → คลาส 1  ที่ x[170,210) y[25,85)   = 2400 px
  [B] ป่า → ถูกถาง/เสื่อม         (NDVI ↓)  → คลาส 2  ที่ x[120,170) y[140,180) = 2000 px
  [C] พืชพรรณ → เมืองขยาย       (NDBI ↑)  → คลาส 3  ที่ x[80,105)  y[0,100)   = 2500 px
  [D] ตึกเก่า → กลับเป็นเขียว     (NDBI ↓)  → คลาส 4  ที่ x[0,25)    y[0,60)    = 1500 px
  ที่เหลือ ไม่เปลี่ยน → คลาส 0 (57136 px)

รัน:  python scripts/make_change_test_tiff.py
ออก:  data/sample/change_t1.tif , change_t2.tif
"""
import os

import numpy as np
import rasterio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "data", "sample")
SIZE = 256
SCALE = 1e4  # 0–10000 reflectance หน่วย/พิกเซล

# แบนด์: Blue Green Red NIR SWIR1 SWIR2
VEG  = np.array([0.035, 0.060, 0.045, 0.420, 0.070, 0.045]) * SCALE
BUILT = np.array([0.150, 0.170, 0.180, 0.220, 0.350, 0.300]) * SCALE
WATER = np.array([0.200, 0.160, 0.120, 0.070, 0.050, 0.045]) * SCALE
BARE  = np.array([0.300, 0.320, 0.340, 0.360, 0.280, 0.260]) * SCALE


def make_t(stamp):
    """สร้างภาพ 6 แบนด์ (H,W,6) float32 ตาม stamp function(y,x)."""
    img = np.zeros((SIZE, SIZE, 6), dtype="float32")
    for y in range(SIZE):
        for x in range(SIZE):
            img[y, x] = stamp(y, x)
    return img


def base_stamp(y, x):
    if y >= 210:                       # แม่น้ำแถวล่าง
        return WATER
    if x < 80 and y < 100:             # ตึกในเมืองมุมบนซ้าย
        return BUILT
    if x >= 150 and y < 100:           # ดินโล่งแถวขวาบน
        return BARE
    return VEG                          # ที่เหลือเป็นพืชพรรณ


def make_t1():
    return make_t(base_stamp)


def make_t2():
    def st(y, x):
        c = base_stamp(y, x)
        if 170 <= x < 210 and 25 <= y < 85:      # [A] โล่ง → เขียวเพิ่ม
            c = VEG
        if 120 <= x < 170 and 140 <= y < 180:    # [B] ป่า → ถาง (เขียวลด)
            c = BARE
        if 80 <= x < 105 and y < 100:            # [C] พืช → เมืองขยาย
            c = BUILT
        if x < 25 and y < 60:                     # [D] ตึกเก่า → เขียว
            c = VEG
        return c
    return make_t(st)


def write(path, arr):
    os.makedirs(OUT_DIR, exist_ok=True)
    transform = rasterio.transform.from_origin(500000.0, 1600000.0, 30.0, 30.0)
    with rasterio.open(
        path, "w", driver="GTiff", height=SIZE, width=SIZE, count=6,
        dtype="float32", crs="EPSG:32648", transform=transform,
    ) as dst:
        dst.write(np.moveaxis(arr, -1, 0))
    print("เขียน:", path)


if __name__ == "__main__":
    write(os.path.join(OUT_DIR, "change_t1.tif"), make_t1())
    write(os.path.join(OUT_DIR, "change_t2.tif"), make_t2())
    print("เสร็จแล้ว — ใช้ geo.greenchange.analyze(change_t1.tif, change_t2.tif) เพื่อเทสต์")