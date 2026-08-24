"""ทดสอบ data adapters (Ticket 04–06) — สนใจผลลัพธ์ NormalizedRow + cache.

ใช้ mock แทน network เป็นหลัก; มี smoke test จริง (network) แยกเป็น marker ต่างหาก
"""
import pytest

from core.normalize import NormalizedRow
from datasources import gistda, nasa_power, open_meteo


class _NR:
    """Fake requests response."""

    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p

    def raise_for_status(self):
        return None


# ---------------- Ticket 04: GISTDA ----------------
class TestGistda:
    def test_hotspot_rows_normalize(self, monkeypatch, tmp_path):
        sample = [
            {"lat": 14.5, "lon": 102.9, "confidence": 97, "satellite": "A",
             "datetime": "2023-04-06 10:00", "lu_name": "อ้อย"},
            {"lat": 15.0, "lon": 103.0, "confidence": 60, "satellite": "N",
             "datetime": "2023-04-06 09:00", "lu_name": "ข้าว"},
        ]
        monkeypatch.setattr(gistda._hs, "fetch_gistda", lambda bbox: sample)
        rows = gistda.hotspot_rows([102.5, 14.0, 103.5, 15.5], use_cache=False)
        assert len(rows) == 2
        r = rows[0]
        assert isinstance(r, NormalizedRow)
        assert r.metric == "hotspot_conf" and r.value == 97 and r.src == "gistda"
        assert r.time == "2023-04-06" and r.meta["satellite"] == "A"

    def test_cache_roundtrip(self, monkeypatch, tmp_path):
        monkeypatch.setattr(gistda._hs, "fetch_gistda", lambda bbox: [
            {"lat": 14.5, "lon": 102.9, "confidence": 80,
             "datetime": "2023-04-06 10:00", "satellite": "A"}])
        import datasources.satellite.gistda as g
        # เรียกครั้งแรก (เขียน cache) แล้วเรียกครั้งที่ 2 จาก cache
        # bbox เดิม, cache ไม่ expire (ttl ใหญ่) และ use_cache=True คืนจาก cache โดยไม่เรียก net
        rows1 = g.hotspot_rows([102.5, 14.0, 103.5, 15.5], use_cache=True, ttl=3600)
        calls = []
        monkeypatch.setattr(g._hs, "fetch_gistda", lambda bbox: calls.append(1) or [])
        rows2 = g.hotspot_rows([102.5, 14.0, 103.5, 15.5], use_cache=True, ttl=3600)
        assert len(rows2) == len(rows1) and not calls  # ไม่ต้องดึง net อีก


# ---------------- Ticket 05: NASA POWER ----------------
class TestNasaPower:
    def test_rows_from_series(self):
        series = {"T2M": {"20230401": 30.2, "20230402": None},
                  "RH2M": {"20230401": 70.0}}
        rows = nasa_power._rows_from_series(10.0, 100.0, series, "power")
        assert len(rows) == 2  # None ถูกข้าม
        t2m = [r for r in rows if r.metric == "power_T2M"][0]
        assert t2m.value == 30.2 and t2m.src == "nasa_power"
        assert t2m.time == "2023-04-01"  # YYYYMMDD → ISO

    def test_fetch_point(self, monkeypatch):
        called = {}
        monkeypatch.setattr(nasa_power, "_fetch", lambda *a, **k: called.update(a=a) or {
            "T2M": {"2023-04-01": 30.0}}) 
        rows = nasa_power.fetch_point(10, 100, "2023-04-01", "2023-04-01",
                                      params=("T2M",), use_cache=False)
        assert rows[0].metric == "power_T2M" and rows[0].lat == 10


# ---------------- Ticket 06: Open-Meteo ----------------
class TestOpenMeteo:
    def test_current(self, monkeypatch):
        payload = {"current_weather": {
            "time": "2023-04-06T12:00", "temperature": 31.0,
            "windspeed": 4.5, "winddirection": 120}}
        monkeypatch.setattr(open_meteo.requests, "get",
                            lambda *a, **k: _NR(payload))
        rows = open_meteo.current(18.0, 99.0, use_cache=False)
        assert len(rows) == 3
        assert rows[0].metric == "openmeteo_temperature" and rows[0].value == 31.0

    def test_hourly_range(self, monkeypatch):
        payload = {"hourly": {
            "time": ["2023-04-06T00:00", "2023-04-06T01:00"],
            "temperature_2m": [30.0, None],
            "precipitation": [0.0, 0.5],
        }}
        monkeypatch.setattr(open_meteo.requests, "get",
                            lambda *a, **k: _NR(payload))
        rows = open_meteo.hourly_range(18.0, 99.0, "2023-04-06", "2023-04-06",
                                       use_cache=False)
        temps = [r for r in rows if r.metric == "openmeteo_temperature"]
        preps = [r for r in rows if r.metric == "openmeteo_precipitation"]
        assert len(temps) == 1 and temps[0].value == 30.0  # None ข้าม
        assert len(preps) == 2