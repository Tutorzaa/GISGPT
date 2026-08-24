# 10 — Raster pixel layer: NDVI/NDBI สีตามคลาส

**What to build:** เมื่อมีภาพดาวเทียม (GeoTIFF) ระบบจัดเป็นชั้น "พิกเซลสี" บนแผนที่ — จำแนกคลาส land cover / ดัชนี (NDVI/NDWI/NDBI) แล้วส่งเป็น layer (ตาราง/GeoJSON หรือ tiles) ให้เห็นเป็นพิกเซลสีตามแบบผู้ใช้ต้องการ (reuse `geo/indices`, `geo/visualize`)

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] service raster → layer (color-class per pixel) + legend
- [ ] ต่อย่อยภาพเป็น tiles/GeoJSON สำหรับแผนที่ขนาดใหญ่
- [ ] pytest กับภาพจำลอง