"""geo/analysis.py — เครื่องมือวิเคราะห์เชิงสถิติ (Phase B: hotspot ↔ คุณภาพอากาศ)

- ระยะทาง Haversine + หาสถานีใกล้สุด
- Cross-sectional: สถานีฝุ่น ↔ hotspot ในรัศมี (จุด/ผลรวมความรุนแรง ต่อสถานี)
- Time-series: อนุกรมรายวัน (FRP รวม ↔ PM2.5 เฉลี่ย) → Pearson r, p-value
- คืนข้อมูล scatter เป็น JSON ให้ front-end วาดกราฟได้
"""
import math

import numpy as np


def haversine_km(lat1, lon1, lat2, lon2):
    """ระยะทางระหว่าง 2 พิกัด (กิโลเมตร)"""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def nearest_stations(lat, lon, stations, k=3):
    """สถานี k อันดับที่ใกล้ที่สุด → list dict {st, distance_km}"""
    with_dist = [
        {**st, "distance_km": round(haversine_km(lat, lon, st["lat"], st["lon"]), 1)}
        for st in stations
    ]
    return sorted(with_dist, key=lambda s: s["distance_km"])[:k]


def pearson(x, y):
    """Pearson correlation → (r, p-value) — ใช้ scipy ถ้ามี ไม่งั้นคำนวณเอง"""
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")
    if len(x) < 3 or len(x) != len(y):
        return 0.0, 1.0, len(x)
    try:
        from scipy import stats

        r, p = stats.pearsonr(x, y)
        return round(float(r), 4), round(float(p), 5), len(x)
    except Exception:
        mx, my = x.mean(), y.mean()
        cov = ((x - mx) * (y - my)).sum()
        sx = math.sqrt(((x - mx) ** 2).sum())
        sy = math.sqrt(((y - my) ** 2).sum())
        if sx == 0 or sy == 0:
            return 0.0, 1.0, len(x)
        r = cov / (sx * sy)
        # p-value โดยประมาณ (t-distribution, n-2 df)
        n = len(x)
        t = r * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
        p = 2 * (1 - _t_cdf(abs(t), n - 2))
        return round(float(r), 4), round(float(p), 5), n


def _t_cdf(t, df):
    """approx CDF ของ t-distribution (ใช้ regularized incomplete beta)"""
    try:
        from scipy.special import betainc

        x = df / (df + t * t)
        return 1 - 0.5 * betainc(df / 2, 0.5, x)
    except Exception:
        return 0.5  # fallback กลาง


def station_hotspot_stats(hotspots, stations, radius_km=60):
    """ต่อสถานี: นับ hotspot + ผลรวม score/FRP ในรัศมี → ใช้ cross-sectional"""
    out = []
    for st in stations:
        near = [
            h
            for h in hotspots
            if haversine_km(st["lat"], st["lon"], h["lat"], h["lon"]) <= radius_km
        ]
        out.append({
            **{k: st[k] for k in ("st_id", "st_name", "lat", "lon", "pm25", "pm10") if k in st},
            "hotspot_count": len(near),
            "hotspot_sum_score": round(sum(h.get("score", h.get("confidence", 0)) for h in near), 1),
            "hotspot_sum_frp": round(sum(h.get("frp", 0) for h in near), 2),
        })
    return out


def cross_sectional_correlation(station_stats, metric="hotspot_count"):
    """สถานีที่มีข้อมูล pm25 จริง → r, p, scatter points {x: hotspot metric, y: pm25}"""
    pts = [
        {"x": s[metric], "y": s["pm25"], "st_name": s["st_name"], "lat": s["lat"], "lon": s["lon"]}
        for s in station_stats
        if isinstance(s.get("pm25"), (int, float)) and not math.isnan(s["pm25"])
    ]
    if len(pts) < 3:
        return {"n": len(pts), "r": 0.0, "p": 1.0, "points": pts, "note": "ข้อมูลน้อยเกินไป (n<3)"}
    r, p, n = pearson([p["x"] for p in pts], [p["y"] for p in pts])
    return {"n": n, "r": r, "p": p, "points": pts, "metric": metric}


def time_series_correlation(dates, hotspot_series, pm25_series):
    """อนุกรมรายวัน 2 ชุด (จับคู่ตามวันที่) → r, p, scatter, n"""
    hm = {d: v for d, v in zip(dates, hotspot_series)}
    pm = {d: v for d, v in zip(dates, pm25_series)}
    common = sorted(set(hm) & set(pm))
    pts = [{"date": d, "hotspot": hm[d], "pm25": pm[d]} for d in common]
    if len(pts) < 3:
        return {"n": len(pts), "r": 0.0, "p": 1.0, "points": pts, "note": "ข้อมูลน้อยเกินไป (n<3)"}
    r, p, n = pearson([p["hotspot"] for p in pts], [p["pm25"] for p in pts])
    return {"n": n, "r": r, "p": p, "points": pts}


def render_scatter(result, out_path, title="", xlabel="", ylabel=""):
    """วาด scatter plot ลง PNG (matplotlib Agg) — สำหรับแสดงในแอป/แชท"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pts = result.get("points", [])
    xs = [p["x"] for p in pts] if "x" in (pts[0] if pts else {}) else [p["hotspot"] for p in pts]
    ys = [p["y"] for p in pts] if "y" in (pts[0] if pts else {}) else [p["pm25"] for p in pts]
    fig, ax = plt.subplots(figsize=(6, 4.2), dpi=110)
    ax.scatter(xs, ys, alpha=0.75, color="#4f8cff", edgecolor="white", linewidth=0.4)
    if len(xs) > 2:
        m, b = np.polyfit(xs, ys, 1)
        ax.plot(xs, [m * x + b for x in xs], "--", color="#34d399", lw=1.2)
    ax.set_title(f"{title}\nr = {result.get('r')}, p = {result.get('p')} (n={result.get('n')})", fontsize=10)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
