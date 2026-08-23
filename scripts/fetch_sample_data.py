"""ดาวน์โหลดภาพดาวเทียมตัวอย่างจริง (best-effort)

ลองดึงจาก Hugging Face dataset ที่เปิดเผย หากสำเร็จจะบันทึกที่ data/raw/
ถ้าไม่สำเร็จ (ต้อง login / ไม่มีเน็ต) ให้ใช้ data/sample/test.tif ที่สร้างจาก
scripts/make_test_tiff.py แทน หรืออัปโหลด Sentinel-2/Landsat ของตัวเอง

แหล่งข้อมูลจริง (สำหรับแล็บ/วิจัย):
- Copernicus Data Space (Sentinel-2 L2A ฟรี ต้องสมัคร): https://dataspace.copernicus.eu
- USGS EarthExplorer (Landsat ฟรี): https://earthexplorer.usgs.gov
"""
import os
import sys

import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")

# ตัวอย่าง: HLS burn scar scene (NASA-IBM) — โมเดล Prithvi ฝึกจาก HLS แบบนี้
CANDIDATES = [
    "https://huggingface.co/datasets/ibm-nasa-geospatial/hls_burn_scars/resolve/main/data/001.tif",
]


def main():
    os.makedirs(RAW, exist_ok=True)
    ok = False
    for url in CANDIDATES:
        name = os.path.basename(url)
        dest = os.path.join(RAW, name)
        try:
            print(f"กำลังลอง: {url}")
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 10_000:
                with open(dest, "wb") as fh:
                    fh.write(r.content)
                print(f"✅ ดาวน์โหลดแล้ว: {dest} ({len(r.content)/1e6:.1f} MB)")
                ok = True
                break
            print(f"  → HTTP {r.status_code} ข้ามไป")
        except Exception as e:
            print(f"  → ผิดพลาด: {e}")

    if not ok:
        print("⚠️ ไม่มีแหล่งข้อมูลที่ใช้ได้ — ใช้ scripts/make_test_tiff.py สร้างภาพจำลองก่อน หรืออัปโหลดภาพจริง")
        sys.exit(1)


if __name__ == "__main__":
    main()
