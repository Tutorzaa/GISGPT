"""scripts/fetch_hotspots.py — ดึง hotspot (GISTDA + FIRMS) ไปไว้ data/processed

รัน:
    python scripts/fetch_hotspots.py --province บุรีรัมย์
    python scripts/fetch_hotspots.py --bbox 102.4,14.1,103.5,15.8 --days 10
ถ้ามีคีย์ FIRMS ตั้ง env:  FIRMS_KEY=xxxx  (หรือ .env)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from geo import hotspots as hs


def main():
    ap = argparse.ArgumentParser(description="ดึงจุดความร้อน")
    ap.add_argument("--province", default="บุรีรัมย์", help="ชื่อจังหวัด (ไทย/อังกฤษ)")
    ap.add_argument("--bbox", help="lon_min,lat_min,lon_max,lat_max (แทน province)")
    ap.add_argument("--days", type=int, default=7, help="ย้อนหลังกี่วัน (FIRMS)")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    if args.bbox:
        bbox = tuple(float(x) for x in args.bbox.split(","))
        hot, from_cache = hs.get_hotspots(bbox, use_cache=not args.no_cache, firms_days=args.days)
        print(f"hotspot ทั้งหมดใน bbox: {len(hot)} (cache={from_cache})")
    else:
        data = hs.province_hotspots(args.province, use_cache=not args.no_cache)
        if "error" in data:
            print("❌", data["error"])
            sys.exit(1)
        s = data["summary"]
        print(f"🏞️ จังหวัด: {s['province']} | จุดในจังหวัด: {s['count']}")
        print(f"   ช่วงวันที่: {s['date_range']}")
        print(f"   แยกแหล่ง: {s['by_source']}")
        print(f"   แยกดาวเทียม: {s['by_satellite']}")
        print(f"   แยกประเภทที่ดิน: {s['by_lu']}")
        print("   อันดับ Top 5:")
        for t in s["top"][:5]:
            print(
                f"     #{t['score']:>6}  ({t['lat']:.4f}, {t['lon']:.4f})  "
                f"{t['datetime']}  {t['satellite']}  {t['lu_name'] or '-'}"
            )
        hot = data["hotspots"]

    os.makedirs(hs.PROC_DIR, exist_ok=True)
    out = os.path.join(hs.PROC_DIR, "hotspots.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(hot, fh, ensure_ascii=False, indent=1)
    print(f"💾 บันทึก {len(hot)} จุด ไปที่ {out}")


if __name__ == "__main__":
    main()
