# 06 — Data adapter: Open-Meteo → NormalizedRow (met ฟรี)

**What to build:** ฝั่ง met ตัวที่สองแบบไม่ต้องคีย์ — ดึงสภาพอากาศปัจจุบัน/ย้อนหลังจาก Open-Meteo (อุณหภูมิ ลม ฝน) ตามพิกัด/bbox แล้วแปลงเป็นแถวมาตรฐาน ใช้เป็นชั้น met ตามต้องการ

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] เรียก Open-Meteo API สำหรับจุด/กริด + ช่วงเวลา
- [ ] normalize → แถวเดียวกับ T05; cache
- [ ] pytest เทียบ Open-Meteo กับ NASA POWER 2 จุด (sanity)