# 05 — Data adapter: NASA POWER → NormalizedRow (met ฟรี)

**What to build:** ผู้ใช้ขอ "สภาพอากาศรายวัน/รายเดือนของพื้นที่" → ดึงจาก NASA POWER API (ฟรี ไม่ต้องคีย์) ตาม bbox/เวลา แล้วแปลงเป็นแถวมาตรฐาน ใช้เป็นฝั่ง met ตัวแรก (อุณหภูมิ ฝน/ความชื้น)

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] เรียก NASA POWER (parameters: T2M, PRECTOTCORR, RH2M …) สำหรับกริด/จุดใน bbox+ช่วงเวลา
- [ ] normalize → `{lat, lon, time, metric:"power_t2m", value, src:"nasa_power"}`
- [ ] cache + จัดการ missing (ฝั่งฟรีมีจุดขาดเป็นปกติ)