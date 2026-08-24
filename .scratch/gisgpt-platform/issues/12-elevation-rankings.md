# 12 — Elevation / mountain ranking (จาก DEM)

**What to build:** ผู้ใช้ถาม "ดู mountain rankings เรียงลำดับ" → ระบบโหลด DEM (SRTM/GMTED) สำหรับ bbox หายอดสูงสุด/จัดอันดับจุด แล้วให้กดดูรายละเอียดแต่ละจุดได้ในขอบเขต

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] ดาวน์โหลด/แคช DEM tile (SRTM 30 ม. ฟรี) สำหรับจังหวัด/ขอบเขตที่ขอ
- [ ] หายอดพีค (peak detection) + จัดอันดับ + ชื่อ/พิกัด
- [ ] API คืนรายการ {rank, lat, lon, elevation} + ตัวอย่างจริง (เช่น เชียงใหม่/ดอย)