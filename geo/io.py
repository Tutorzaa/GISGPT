"""geo.io — อ่าน/เขียน GeoTIFF และจัดการไฟล์อัปโหลด

โค้ดส่วนนี้รับผิดชอบข้อมูลเชิงพื้นที่ (raster) ทั้งหมด:
- บันทึกไฟล์ที่ผู้ใช้อัปโหลด
- อ่าน raster เป็น numpy array (H, W, C) พร้อม metadata
- คำนวณพื้นที่ต่อพิกเซล (m²) จาก geotransform
"""
import os
import uuid

import numpy as np
import rasterio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")


def save_upload(file_storage):
    """บันทึกไฟล์อัปโหลดลง data/raw แล้วคืนข้อมูลสรุป (bands, ขนาด, CRS)."""
    os.makedirs(DATA_RAW, exist_ok=True)
    fid = uuid.uuid4().hex[:12]
    path = os.path.join(DATA_RAW, fid + ".tif")
    file_storage.save(path)
    info = probe(path)
    info["file_id"] = fid
    info["path"] = path
    info["name"] = file_storage.filename
    return info


def probe(path):
    """อ่านเฉพาะ metadata ของ GeoTIFF."""
    with rasterio.open(path) as src:
        return dict(
            bands=src.count,
            width=src.width,
            height=src.height,
            crs=str(src.crs),
            dtype=str(src.dtypes[0]),
            transform=[round(float(v), 6) for v in src.transform][:6],
        )


def read_tiff(path):
    """อ่าน raster เป็น float32 array รูปทรง (H, W, C) พร้อม meta."""
    with rasterio.open(path) as src:
        arr = src.read()
        meta = dict(
            width=src.width,
            height=src.height,
            count=src.count,
            crs=src.crs,
            transform=src.transform,
            dtype=str(src.dtypes[0]),
        )
    arr = np.moveaxis(arr, 0, -1).astype("float32")  # (C,H,W) -> (H,W,C)
    return arr, meta


def pixel_area_m2(meta):
    """พื้นที่ต่อพิกเซล (ตารางเมตร) จาก geotransform; คืน None ถ้าหาไม่ได้."""
    try:
        t = meta["transform"]
        return abs(t.a * t.e)
    except Exception:
        return None


def write_tiff(path, arr, meta):
    """เขียน array (H, W, C) กลับเป็น GeoTIFF (คัดลอก profile จาก meta)."""
    data = np.moveaxis(arr, -1, 0).astype("float32")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=meta["height"],
        width=meta["width"],
        count=data.shape[0],
        dtype="float32",
        crs=meta.get("crs"),
        transform=meta["transform"],
    ) as dst:
        dst.write(data)
    return path
