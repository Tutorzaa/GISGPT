"""scripts/fetch_phaseb.py — Phase B: วิเคราะห์ hotspot ↔ PM2.5

โหมด 1 — Cross-sectional (วันเดียว, ทั่วประเทศ):
    python scripts/fetch_phaseb.py --date 2020-08-29 --radius 100
      FIRMS archive (วันนั้น) + GISTDA AQ (70 สถานี วันเดียวกัน)
      → ต่อสถานี: hotspot ในรัศมี vs PM2.5 → Pearson r, p + scatter PNG

โหมด 2 — Time-series (รายวัน, จังหวัด):
    python scripts/fetch_phaseb.py --timeseries บุรีรัมย์ --start 2023-04-01 --end 2023-04-30
      FIRMS archive รายวัน (FRP รวม) + CAMS EAC4 PM2.5 (ศูนย์กลางจังหวัด)
      → correlation รายวัน + scatter PNG

ต้องมีคีย์ใน environment: FIRMS_KEY (โหมด 1-2), .cdsapirc CAMS (โหมด 2)
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# โหลด .env (คีย์ API) ถ้ามี
_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env):
    for line in open(_env, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from geo import airquality as aq
from geo import analysis as an
from geo import hotspots as hs

TH_BBOX = (97.3, 5.5, 105.8, 20.5)


def cross_sectional(date, radius, out_prefix):
    aq_stations = aq.fetch_gistda_aq()
    print(f"📡 สถานี AQ: {len(aq_stations)} (วันที่: {aq_stations[0]['datetime'] if aq_stations else '?'})")

    hotspots, src = aq.fetch_firms_archive(TH_BBOX, date)
    hs2, src2 = aq.fetch_firms_archive(TH_BBOX, date, dataset="MODIS_SP")
    hotspots.extend(hs2)
    print(f"🔥 hotspot FIRMS archive {date}: {len(hotspots)} จุด (VIIRS={len(hotspots)-len(hs2)}, MODIS={len(hs2)})")
    for h in hotspots:
        h["score"] = h["frp"] if h["frp"] > 0 else h["confidence"]

    stats = an.station_hotspot_stats(hotspots, aq_stations, radius_km=radius)
    valid = sum(1 for s in stats if s["hotspot_count"] > 0 and s["pm25"] is not None)
    print(f"🏭 สถานีที่มี hotspot ในรัศมี {radius}กม. + มี pm25: {valid}/{len(stats)}")

    for metric in ("hotspot_count", "hotspot_sum_frp"):
        res = an.cross_sectional_correlation(stats, metric=metric)
        print(f"📊 correlation {metric} vs PM2.5: r={res['r']}, p={res['p']} (n={res['n']})")
        if res["n"] >= 3:
            out = f"outputs/phaseb_{out_prefix}_{metric}.png"
            an.render_scatter(res, out, title=f"Hotspot ({metric}) vs PM2.5 — {date}",
                              xlabel=metric, ylabel="PM2.5 (µg/m³)")
            print(f"   📈 scatter: {out}")

    with open(f"data/processed/phaseb_{out_prefix}.json", "w", encoding="utf-8") as fh:
        json.dump({"date": date, "radius_km": radius, "station_stats": stats}, fh, ensure_ascii=False, indent=1)


def time_series(province, start, end, out_prefix):
    feature, pname = hs.find_province(province)
    if feature is None:
        print("❌ ไม่พบจังหวัด", province)
        sys.exit(1)
    bbox = hs.province_bbox(feature, margin=1.0)  # ควันเดินทางข้ามจังหวัด — ใช้พื้นที่กว้าง 1°
    lon = (bbox[0] + bbox[2]) / 2
    lat = (bbox[1] + bbox[3]) / 2
    print(f"📍 {pname} — bbox {bbox}, centroid ({lat:.3f}, {lon:.3f})")

    # hotspot รายวัน
    days = []
    d = dt.date.fromisoformat(start)
    end_d = dt.date.fromisoformat(end)
    while d <= end_d:
        hs_day, _ = aq.fetch_firms_archive(bbox, d.isoformat())
        days.extend(hs_day)
        d += dt.timedelta(days=1)
    series = aq.daily_series(days)
    print(f"🔥 hotspot รวม {len(days)} จุด ({len(series)} วัน)")

    # PM2.5 รายวัน (CAMS)
    pm, src = aq.fetch_cams_daily_pm25(lat, lon, start, end)
    print(f"🌫️ CAMS PM2.5: {len(pm)} วัน (source={src})")
    if not pm:
        print("⚠️ ยังไม่มีข้อมูล CAMS (ตรวจ .cdsapirc) — ข้าม correlation")
        return

    res = an.time_series_correlation(
        [x["date"] for x in pm], [series.get(x["date"], {}).get("sum_frp", 0) for x in pm],
        [x["pm25"] for x in pm],
    )
    print(f"📊 correlation FRP รวม/วัน vs PM2.5/วัน: r={res['r']}, p={res['p']} (n={res['n']})")
    if res["n"] >= 3:
        out = f"outputs/phaseb_{out_prefix}_timeseries.png"
        an.render_scatter(res, out, title=f"Hotspot FRP vs PM2.5 — {pname} ({start}→{end})",
                          xlabel="FRP รวม/วัน", ylabel="PM2.5 (µg/m³)")
        print(f"   📈 scatter: {out}")
    with open(f"data/processed/phaseb_{out_prefix}_ts.json", "w", encoding="utf-8") as fh:
        json.dump({"province": pname, "start": start, "end": end, "result": res,
                   "daily": [{"date": k, **v} for k, v in sorted(series.items())],
                   "pm25": pm}, fh, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser(description="Phase B: hotspot ↔ PM2.5")
    ap.add_argument("--date", help="cross-sectional: วันที่ (YYYY-MM-DD) ที่มีทั้ง hotspot + AQ")
    ap.add_argument("--radius", type=float, default=100, help="รัศมีสถานี (กม.)")
    ap.add_argument("--timeseries", help="time-series: ชื่อจังหวัด")
    ap.add_argument("--start", help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD")
    args = ap.parse_args()

    if args.date:
        cross_sectional(args.date, args.radius, args.date.replace("-", ""))
    elif args.timeseries:
        time_series(args.timeseries, args.start, args.end, args.timeseries)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
