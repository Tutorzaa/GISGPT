# 20 — Benchmark: นิยามงานเชิงพื้นที่-เวลา (known events)

**What to build:** สร้างชุดโจทย์ benchmark สำหรับวิจัย — เหตุการณ์เชิงพื้นที่-เวลาที่รู้คำตอบจริง (จากข้อมูลจริง เช่น hotspot/ฝุ่น เดือนเผา) ใช้ทดสอบว่า GFM/ระบบวิเคราะห์ "ยืนยันเหตุการณ์" ได้ตรงแค่ไหน

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] นิยามงาน (task) เช่น: detect จุดไฟ, เปรียบเทียบฝุ่น pre/post, change event
- [ ] dataset + ground-truth (เก็บเป็นไฟล์/JSON พร้อม metadata แหล่ง)
- [ ] เกณฑ์ผ่าน/ไม่ผ่านของแต่ละงาน