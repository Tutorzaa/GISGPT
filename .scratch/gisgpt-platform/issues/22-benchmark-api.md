# 22 — API benchmark + รายงาน verify

**What to build:** ผู้ใช้/นักวิจัยเปิด `/api/benchmark` เห็นผลการประเมิน (เมตริกต่อ task, สรุป) + รายงาน "ระบบวิเคราะห์เหตุการณ์ spatio-temporal ถูกต้องแค่ไหน / verify ความเข้าใจโมเดล" เป็นเอกสารสรุป

**Blocked by:** 21

**Status:** ready-for-agent

- [ ] route `GET /api/benchmark` → สรุปผล + ลิงก์รายงาน
- [ ] เขียน `docs/BENCHMARK_REPORT.md` (ผล real + ข้อจำกัด/ข้อเสนอ)