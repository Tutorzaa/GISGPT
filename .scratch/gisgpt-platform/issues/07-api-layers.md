# 07 — API: /api/layers + /api/layers/<name>

**What to build:** ผู้เรียก (frontend/อีก API) เปิด `/api/layers` เห็นชั้นข้อมูลที่แพลตฟอร์มมี (hotspot, อุณหภูมิ, ฝน, ฝุ่น…) พร้อม metadata แล้วเปิด `/api/layers/<name>?bbox&time&res` เอาข้อมูลเป็น GeoJSON/data points สำหรับวาดบนแผนที่

**Blocked by:** 01, 04, 05, 06

**Status:** ready-for-agent

- [ ] `/api/layers` → รายการ metadata (metric, src, ประเภท, ช่วงเวลาที่มี)
- [ ] `/api/layers/<name>` → GeoJSON FeatureCollection ของ NormalizedRow (bbox/time/res)
- [ ] ใช้ cache ชั้นเดียวกัน; json schema เอกสารใน `docs/BACKEND_STRUCTURE.md`