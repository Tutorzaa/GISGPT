"""ทดสอบ core (Ticket 01): NormalizedRow schema + JSONCache."""
import os
import time

import pytest

from core import cache as cache_mod
from core import normalize as nz


# ---------- NormalizedRow schema ----------
class TestNormalizedRow:
    def test_valid_row_and_to_dict(self):
        r = nz.make(18.9, 98.9, "2023-04-05", "hotspot_frp", 84.0, "gistda", {"conf": 90})
        d = r.to_dict()
        assert d["lat"] == 18.9 and d["lon"] == 98.9
        assert d["metric"] == "hotspot_frp" and d["value"] == 84.0 and d["meta"]["conf"] == 90

    def test_type_coercion(self):
        r = nz.make("18.5", "98.5", 20230405, "power_t2m", "31.2", "nasa_power")
        assert isinstance(r.lat, float) and isinstance(r.value, float)
        assert r.time == "20230405"

    @pytest.mark.parametrize("lat", [-90.1, 90.01, 999, -999])
    def test_lat_out_of_range_raises(self, lat):
        with pytest.raises(ValueError):
            nz.make(lat, 0, "t", "m", 1, "s")

    @pytest.mark.parametrize("lon", [-180.1, 180.01])
    def test_lon_out_of_range_raises(self, lon):
        with pytest.raises(ValueError):
            nz.make(0, lon, "t", "m", 1, "s")

    @pytest.mark.parametrize("field", ["metric", "src", "time"])
    def test_required_fields_nonempty(self, field):
        kw = dict(lat=0, lon=0, time="t", metric="m", value=1, src="s")
        kw[field] = ""
        with pytest.raises(ValueError):
            nz.make(**kw)

    def test_from_dict_roundtrip(self):
        r = nz.make(15.1, 102.6, "2023-04-06", "cams_pm25", 45.2, "cams_eac4")
        assert nz.from_dict(r.to_dict()) == r

    def test_to_geojson(self):
        rows = [nz.make(1, 2, "t", "m", 5, "s"), nz.make(3, 4, "t", "m", 6, "s")]
        gj = nz.to_geojson(rows)
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 2
        assert gj["features"][0]["geometry"]["coordinates"] == [2, 1]
        assert gj["features"][0]["properties"]["value"] == 5


# ---------- JSONCache ----------
@pytest.fixture()
def tmp_cache(tmp_path):
    return cache_mod.JSONCache(cache_dir=str(tmp_path), ttl=None)


class TestJSONCache:
    def test_set_get_roundtrip(self, tmp_cache):
        tmp_cache.set("a", {"x": 1, "nested": [1, 2, 3]})
        assert tmp_cache.get("a") == {"x": 1, "nested": [1, 2, 3]}

    def test_get_missing_returns_none(self, tmp_cache):
        assert tmp_cache.get("nope") is None

    def test_key_is_stable_and_safe(self, tmp_cache):
        k1 = tmp_cache._key("firms", "hotspot", "102.6,14.4")
        k2 = tmp_cache._key("firms", "hotspot", "102.6,14.4")
        assert k1 == k2
        assert "/" not in k1 and "\\" not in k1

    def test_delete(self, tmp_cache):
        tmp_cache.set("b", 1)
        tmp_cache.delete("b")
        assert tmp_cache.get("b") is None

    def test_ttl_expiry(self, tmp_path):
        c = cache_mod.JSONCache(cache_dir=str(tmp_path), ttl=10)
        c.set("k", "v")
        assert c.get("k") == "v"
        old = time.time() - 100
        os.utime(c._path("k"), (old, old))
        assert c.get("k") is None

    def test_clear(self, tmp_cache):
        tmp_cache.set("a", 1)
        tmp_cache.set("b", 2)
        assert tmp_cache.clear() >= 2
        assert tmp_cache.get("a") is None and tmp_cache.get("b") is None