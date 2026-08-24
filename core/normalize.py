"""core.normalize — schema แถวมาตรฐาน (NormalizedRow) สำหรับทุกแหล่งข้อมูล


เป็น "สะพาน" ให้ทั้งข้อมูลดาวเทียมและสภาพอากาศรวมกันได้ในชุดแถวเดียว
จากนั้น spatial join / correlation / เปรียบเทียบเวลา ทำได้บนชุดเดียวกัน
(ดู docs/PLATFORM_ARCHITECTURE.md §2)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

_LAT_OK = (-90.0, 90.0)
_LON_OK = (-180.0, 180.0)


@dataclass(frozen=True)
class NormalizedRow:
    """หนึ่งจุดข้อมูลมาตรฐาน.

    - metric: ตัวระบุสิ่งที่วัด เช่น "hotspot_frp", "power_t2m", "cams_pm25"
    - src:    แหล่งที่มา เช่น "gistda", "nasa_power", "open_meteo", "cams_eac4"
    - meta:   ข้อมูลเสริม (satellite, confidence, ฯลฯ) ใช้ได้ไม่ขึ้นกับใคร
    """
    lat: float
    lon: float
    time: str                      # ISO datetime/date (str)
    metric: str
    value: float
    src: str
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        if not (_LAT_OK[0] <= self.lat <= _LAT_OK[1]):
            raise ValueError(f"lat เกินขอบเขต: {self.lat}")
        if not (_LON_OK[0] <= self.lon <= _LON_OK[1]):
            raise ValueError(f"lon เกินขอบเขต: {self.lon}")
        if not (self.metric and self.src and self.time):
            raise ValueError("metric/src/time ต้องไม่ว่าง")

    def to_dict(self) -> dict:
        return asdict(self)


def make(lat, lon, time, metric, value, src, meta=None) -> NormalizedRow:
    """สร้าง NormalizedRow พร้อมค่า meta ตก default."""
    return NormalizedRow(lat=float(lat), lon=float(lon), time=str(time),
                         metric=str(metric), value=float(value), src=str(src),
                         meta=meta or {})


def to_records(rows: Iterable[NormalizedRow]) -> list[dict]:
    """แปลงชุดแถว → list ของ dict (สำหรับ JSON/API)."""
    return [r.to_dict() for r in rows]


_KEYS = ("lat", "lon", "time", "metric", "value", "src")


def from_dict(d: dict) -> NormalizedRow:
    """สร้าง NormalizedRow จาก dict เดิม (เป็นระเบียบ)."""
    return NormalizedRow(**{k: d[k] for k in _KEYS}, meta=d.get("meta", {}))


def to_geojson(rows: Iterable[NormalizedRow]) -> dict:
    """แปลงชุดแถว → GeoJSON FeatureCollection (สำหรับวาดบนแผนที่)."""
    feats = []
    for r in rows:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
            "properties": {"metric": r.metric, "value": r.value,
                           "src": r.src, "time": r.time, **r.meta},
        })
    return {"type": "FeatureCollection", "features": feats}