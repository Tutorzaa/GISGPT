# 11 — Change-detection layer (2 ช่วงเวลา)

**What to build:** ผู้ใช้ให้ภาพ 2 ช่วงเวลาของพื้นที่เดียวกัน → สร้าง layer "การเปลี่ยนแปลง" (เขียวเพิ่ม/ลด, เมืองขยาย/ลด) เป็นพิกเซลสี + สถิติพื้นที่ + ผลสุทธิ (reuse `geo/greenchange.py`) — ใช้ได้กับโจทย์ "ต่างช่วงเวลา"

**Blocked by:** 10

**Status:** ready-for-agent

- [ ] API รับ t1/t2 GeoTIFF → กลับ change layer + stats (มี `/api/greenchange` แล้ว → ปรับเข้า layer schema)
- [ ] ส่ง legend 5 คลาส; แยก/metric ผลสุทธิ