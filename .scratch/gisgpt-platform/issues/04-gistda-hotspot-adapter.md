# 04 — Data adapter: GISTDA hotspot → NormalizedRow

**What to build:** ผู้ใช้ขอ "จุดไฟใน<b>จังหวัด</b>" → ตะลึงย้อนกรองข้อมูล hotspot จาก GISTDA ตามวันที่/ขอบเขต แล้วแปลงเป็นแถวมาตรฐาน `{lat, lon, time, metric:"hotspot_frp", value, src:"gistda"}` (ใช้ได้โดยไม่ต้องคีย์)

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] ดึง GISTDA `FR_Fire/hotspot_daily` → normalize เป็นแถวเดียว
- [ ] กรองโพลิกอนจังหวัด + จัดอันดับ FRP (reuse `geo/hotspots.py`)
- [ ] cache ผล 1 ชม. + ตอบ `{"rows":[...], "count":N, "top":[...]}`