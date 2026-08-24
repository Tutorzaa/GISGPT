"""ดาวน์โหลดภาพ Sentinel-2 L2A 2 ช่วงเวลา จาก Copernicus Data Space (Phase C)

ใช้ STAC API (metadata หาได้ฟรี ไม่ต้อง login) แล้วโหลดแบนด์ที่ต้องใช้ลงมา
เป็น GeoTIFF 6 แบนด์ ลำดับ [B02,B03,B04,B08,B11,B12] = Blue,Green,Red,NIR,SWIR1,SWIR2
ซึ่งตรงกับ geo/indices._bands (ใช้คำนวณ NDVI/NDBI + ระบบเปลี่ยนพื้นที่).

⚠ การ "โหลดแบนด์" (download) ต้องมีบัญชี Copernicus Data Space:
    https://dataspace.copernicus.eu  → OAuth credentials
    ตั้งใน .env:
        COPERNICUS_USER=<อีเมล>
        COPERNICUS_PASSWORD=<รหัสผ่าน>
    (ใช้ OAuth2 client-credentials → Bearer token → ดึงผ่าน S3 over HTTPS)

วิธีใช้
------
    # 1) ค้นหา/จัดอันดับภาพ (ไม่ต้อง login) สำหรับ bbox บุรีรัมย์ 2 ช่วง
    python scripts/fetch_stac_sentinel2.py --bbox 102.6 14.4 103.4 15.4 \
        --periods 2023-03-15,2023-03-31  2023-04-06,2023-04-20 \
        --cloud 25 --search-only

    # 2) โหลดแบนด์จริง (ต้องมี COPERNICUS_USER/PASSWORD ใน .env)
    python scripts/fetch_stac_sentinel2.py --bbox 102.6 14.4 103.4 15.4 \
        --periods 2023-03-15,2023-03-31  2023-04-06,2023-04-20 --cloud 25 \
        --out data/raw/s2_change --resample 10

ออก:  <out>/t1/<bands>.tif  และ  <out>/t2/...   (เรียงแบนด์ B02..B12)
      พร้อม metadata JSON (พิกัด bbox, ช่วงเวลา, คลาวด์, item id)

หมายเหตุ: แบนด์ 20 ม. (B11/B12) จะถูก resample เป็น 10 ม.เมื่อ --resample 10
"""
import argparse
import json
import os
import sys

import requests

STAC_SEARCH = "https://catalogue.dataspace.copernicus.eu/stac/search"
STAC_COLLECTION = "sentinel-2-l2a"
# แบนด์ที่ต้องใช้ (สอดคล้อง geo.indices): Blue Green Red NIR SWIR1 SWIR2
BANDS = [
    ("B02", "s2_b02_blue"), ("B03", "s2_b03_green"), ("B04", "s2_b04_red"),
    ("B08", "s2_b08_nir"), ("B11", "s2_b11_swir1"), ("B12", "s2_b12_swir2"),
]
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
S3_HTTPS = "https://eodata.dataspace.copernicus.eu"


def _load_env():
    """โหลด .env (ไม่ทับตัวแปรที่มีอยู่) — โลจิกลอกตาม main.py."""
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def search_items(bbox, start, end, max_cloud=30, limit=10):
    """STAC POST search → รายการ items ของ Sentinel-2 L2A (ไม่ต้อง login)."""
    params = {
        "collections": [STAC_COLLECTION],
        "bbox": [float(b) for b in bbox],
        "datetime": f"{start}T00:00:00Z/{end}T00:00:00Z",
        "limit": limit,
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
    }
    r = requests.post(STAC_SEARCH, json=params, timeout=60)
    r.raise_for_status()
    feats = r.json().get("features", [])
    out = []
    for f in feats:
        p = f["properties"]
        assets = f.get("assets", {})
        s3 = {k: v.get("href", "") for k, v in assets.items() if v.get("href", "").startswith("s3://")}
        out.append({
            "id": f["id"],
            "datetime": p.get("datetime"),
            "cloud": round(p.get("eo:cloud_cover") or 0, 2),
            "geometry": f.get("geometry"),
            "assets": s3,
        })
    out.sort(key=lambda d: d["cloud"])
    return out


def _bearer():
    """OAuth2 client-credentials token (ต้องมีผู้ใช้/รหัสผ่านใน .env)."""
    user = os.environ.get("COPERNICUS_USER")
    pwd = os.environ.get("COPERNICUS_PASSWORD")
    if not user or not pwd:
        raise RuntimeError(
            "ต้องตั้ง COPERNICUS_USER / COPERNICUS_PASSWORD ใน .env ก่อนโหลดแบนด์จริง "
            "(สมัครได้ฟรีที่ dataspace.copernicus.eu)"
        )
    r = requests.post(TOKEN_URL, data={
        "grant_type": "password", "username": user, "password": pwd,
        "client_id": "cdse-public",
    }, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def _s3_to_https(asset):
    """แปลง s3://eodata/<path> → https://eodata.dataspace.copernicus.eu/<path>."""
    if asset.startswith("s3://eodata/"):
        return S3_HTTPS + "/" + asset[len("s3://eodata/"):]
    return asset


def _resample_on_grid(src_path, ref_meta):
    """อ่านแบนด์ src แล้วจัดพิกเซลให้เป็นกริดของแบนด์อ้างอิง (10 ม.)."""
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    with rasterio.open(src_path) as src:
        arr = src.read(1).astype("float32")
        same = (src.transform == ref_meta["transform"] and src.crs == ref_meta["crs"]
                and src.height == ref_meta["height"] and src.width == ref_meta["width"])
        if same:
            return arr
        dst = np.zeros((ref_meta["height"], ref_meta["width"]), dtype="float32")
        reproject(
            source=arr, destination=dst,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref_meta["transform"], dst_crs=ref_meta["crs"],
            resampling=Resampling.bilinear,
        )
        return dst


def download_product(item, out_dir, resample=10, token=None):
    """เลือก item → ดาวน์โหลด 6 แบนด์ (B02..B12) → ประกอบเป็น GeoTIFF 6 แบนด์.

    ใช้ไฟล์แบนด์ความละเอียดสูงสุดที่มี (B02/B03/B04/B08 =10ม., B11/B12=20ม.)
    แล้ว resample (bilinear) ขึ้นกริดเดียว (default 10 ม.) → เขียน bands.tif
    """
    import os

    import numpy as np
    import rasterio
    from rasterio.enums import Resampling

    token = token or _bearer()
    headers = {"Authorization": f"Bearer {token}"}
    os.makedirs(out_dir, exist_ok=True)

    assets = item["assets"]
    ref_transform = ref_crs = ref_h = ref_w = None
    band_files = []
    for bname, _label in BANDS:
        key = None
        for suffix in ("_10m", "_20m", "_60m"):
            if f"{bname}{suffix}" in assets:
                key = f"{bname}{suffix}"
                break
        if key is None:
            print(f"  ! ข้าม {bname} — ไม่พบ asset {bname}*")
            continue
        url = _s3_to_https(assets[key])
        print(f"  โหลด {key}: {url[:75]}…")
        rr = requests.get(url, headers=headers, timeout=300)
        rr.raise_for_status()
        band_tif = os.path.join(out_dir, f"{bname}.tif")
        with open(band_tif, "wb") as fh:
            fh.write(rr.content)
        band_files.append((bname, band_tif))
        if ref_transform is None:
            with rasterio.open(band_tif) as ref_src:
                ref_transform = ref_src.transform
                ref_crs = ref_src.crs
                ref_h, ref_w = ref_src.height, ref_src.width

    if not band_files:
        raise RuntimeError("ไม่พบแบนด์ที่ดาวน์โหลดได้")

    ref_meta = {"transform": ref_transform, "crs": ref_crs, "height": ref_h, "width": ref_w}
    stack = []
    for bname, path in band_files:
        arr = _resample_on_grid(path, ref_meta)
        stack.append(arr)
        os.remove(path)

    final = np.stack(stack, axis=-1).astype("float32")     # (H,W,6)
    out_tif = os.path.join(out_dir, "bands.tif")
    with rasterio.open(
        out_tif, "w", driver="GTiff", height=ref_h, width=ref_w, count=final.shape[2],
        dtype="float32", crs=ref_crs, transform=ref_transform,
    ) as dst:
        dst.write(np.moveaxis(final, -1, 0))
    return out_tif


def main():
    _load_env()
    ap = argparse.ArgumentParser(description="Sentinel-2 L2A 2 ช่วงเวลา (Phase C) — Copernicus STAC")
    ap.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("LON1", "LAT1", "LON2", "LAT2"))
    ap.add_argument("--periods", nargs="+", required=True,
                    help="ช่วงเวลา 'START,END' 2 ช่วง (เช่น '2023-03-15,2023-03-31')")
    ap.add_argument("--cloud", type=float, default=30, help="คลาวด์สูงสุด %")
    ap.add_argument("--search-only", action="store_true", help="แค่ค้นหา/จัดอันดับ ไม่โหลดแบนด์")
    ap.add_argument("--out", default="data/raw/s2_change")
    ap.add_argument("--resample", type=float, default=10, help="ความละเอียดปลายทาง (เมตร)")
    args = ap.parse_args()

    if len(args.periods) < 2:
        sys.exit("ต้องระบุอย่างน้อย 2 ช่วงเวลา (t1, t2)")

    results = {}
    for i, period in enumerate(args.periods[:2], start=1):
        start, end = period.split(",")
        label = f"t{i}"
        print(f"\n=== {label}: {start} → {end} ===")
        items = search_items(args.bbox, start, end, max_cloud=args.cloud)
        if not items:
            print("  ไม่พบภาพในเกณฑ์คลาวด์ — ลอง --cloud สูงขึ้น")
            results[label] = None
            continue
        best = items[0]
        print(f"  คลาวด์ต่ำสุด: {best['cloud']}%  id={best['id']}")
        for it in items[:5]:
            print(f"    cloud {it['cloud']:5.2f}%  {it['datetime'][:10]}  {it['id']}")
        results[label] = best

        if not args.search_only:
            out_dir = os.path.join(args.out, label)
            os.makedirs(out_dir, exist_ok=True)
            try:
                tif = download_product(best, out_dir, resample=args.resample)
                print(f"  ✅ เขียน -> {tif}")
            except SystemExit:
                raise
            except Exception as e:
                print(f"  ⚠ ไม่ได้โหลด (ดู .env/เครือข่าย): {e}")

    # metadata ผลลัพธ์
    os.makedirs(args.out, exist_ok=True)
    meta = {
        "bbox": ", ".join(str(b) for b in args.bbox),
        "cloud_max": args.cloud,
        "periods": {k: v["datetime"] if v else None for k, v in results.items()},
        "items": {k: v["id"] if v else None for k, v in results.items()},
    }
    with open(os.path.join(args.out, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print("\nบันทึก metadata ->", os.path.join(args.out, "meta.json"))


if __name__ == "__main__":
    main()