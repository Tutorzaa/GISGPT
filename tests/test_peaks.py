"""ทดสอบ analysis.peaks (Ticket 12) — หายอดจากกริดความสูงจำลอง."""
from analysis import peaks
from core.normalize import make


def build():
    """กริด 12x12 (step 0.1° ≈ 11km), ฐาน 100:
    ยอด A(2,2)=2500, ยอด B(9,9)=1500 — ห่างกัน >100km ไม่ครอบกัน"""
    rows = []
    for y in range(12):
        for x in range(12):
            e = 100.0
            dA = abs(x - 2) + abs(y - 2)
            dB = abs(x - 9) + abs(y - 9)
            if dA <= 1:
                e = max(e, 2500 - 500 * dA)
            if dB <= 1:
                e = max(e, 1500 - 300 * dB)
            rows.append(make(10 + y * 0.1, 100 + x * 0.1, "static", "elevation_m",
                             e, "srtm90m"))
    return rows


class TestFindPeaks:
    def test_finds_two_peaks_ordered(self):
        res = peaks.find_peaks(build(), min_elev=300, neighbor_km=40)
        assert len(res) >= 2
        assert res[0]["elev"] >= res[1]["elev"]
        assert res[0]["elev"] > 2000 and res[1]["elev"] > 1000

    def test_ranks_highest_first(self):
        res = peaks.find_peaks(build(), min_elev=300, neighbor_km=40)
        assert abs(res[0]["elev"] - 2500) < 5
        assert abs(res[1]["elev"] - 1500) < 5

    def test_min_elev_filters(self):
        res = peaks.find_peaks(build(), min_elev=2000, neighbor_km=40)
        assert all(p["elev"] >= 2000 for p in res)
        assert len(res) == 1