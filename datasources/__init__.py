"""datasources — ชั้น data adapters (Ticket 04–06)

ทุก adapter รับ "อะไรที่ระบุพื้นที่/เวลา" → คืน `list[NormalizedRow]`
แปลงจากแหล่ง (ดาวเทียม/met/terrain) ผ่าน core.normalize ให้ schema เดียวกัน
และใช้ core.cache ลดการโหลด API ซ้ำ
"""
from core.normalize import NormalizedRow

# ตัวย่อสำหรับเริ่มต้นใช้ (เทียบ geopandas โหลดจาก adapters)
from .satellite import gistda
from .met import nasa_power, open_meteo

__all__ = ["gistda", "nasa_power", "open_meteo", "NormalizedRow"]