# 02 — Geometry utils (bbox/point-in-polygon/grid/haversine)

**What to build:** ชุดเครื่องมือเรขาคณิตที่ทุกงานวิเคราะห์ต้องใช้: สร้าง bbox, ตรวจจุดในโพลิกอน (shapely), สุ่ม/สร้างกริดพิกเซล, ระยะ haversine, buffer จุด — เรียกใช้ซ้ำได้จากทั้ง data adapter และ analysis

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `point_in_polygon`, `bbox_center`, `bbox_grid(res)`, `haversine`, `buffer_km`
- [ ] ครอบด้วย shapely/geopandas; pytest กับข้อมูลเทียบมือ
- [ ] โหลดขอบเขต 77 จังหวัดไทยครั้งเดียว (แคช) — reuse จาก `geo/hotspots`