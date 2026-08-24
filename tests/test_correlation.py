"""ทดสอบ analysis.correlation (Ticket 08) — จับคู่ + r/p บน NormalizedRow"""
from analysis import correlation as corr
from core.normalize import make

D = "2023-04-05"


def ax(n, scale=1.0, base=0.0):
    return [make(10 + i * 0.1, 100.0, D, "power_T2M", base + scale * i, "nasa_power")
            for i in range(n)]


def bx(n, base=0.0, slope=2.0):
    return [make(10 + i * 0.1, 100.0, D, "hotspot_conf", base + slope * i, "gistda")
            for i in range(n)]


class TestMatch:
    def test_matches_near_points(self):
        pairs = corr.match_rows(ax(5), ax(5), radius_km=50)
        assert len(pairs) == 5

    def test_skip_far_points(self):
        far = [make(40.0, 100.0, D, "hotspot_conf", 5, "gistda")]  # 30° ห่าง (≈3300 กม.)
        pairs = corr.match_rows(ax(3), far, radius_km=50)
        assert pairs == []


class TestCrossSectional:
    def test_positive_correlation(self):
        res = corr.cross_sectional(ax(10), bx(10, slope=2.0), metric_a="temp", metric_b="hs")
        assert res["n"] == 10
        assert res["r"] > 0.9 and res["p"] < 0.01

    def test_low_correlation_when_unrelated(self):
        # slope=0 → ค่า b คงที่ → |r| ต้องเล็กมาก
        res = corr.cross_sectional(ax(10), bx(10, base=5.0, slope=0.0), radius_km=50)
        assert abs(res["r"]) < 0.5

    def test_too_few_raises_note(self):
        res = corr.cross_sectional(ax(2), bx(2))
        assert res["n"] < 3 and res["note"] and res["r"] == 0.0


class TestTimeSeries:
    def test_daily_correlation(self):
        dates_a = [make(20, 100, f"2023-04-{d:02d}", "power_T2M", 25 + d, "nasa_power")
                   for d in range(1, 6)]
        dates_b = [make(20, 100, f"2023-04-{d:02d}", "hotspot_conf", 5 + 2 * d, "gistda")
                   for d in range(1, 6)]
        res = corr.time_series(dates_a, dates_b, metric_a="temp", metric_b="hs")
        assert res["mode"] == "time" and res["r"] > 0.9