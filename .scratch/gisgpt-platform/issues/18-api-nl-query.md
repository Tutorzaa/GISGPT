# 18 — API: /api/query (ภาษาไทย → data point + layer + chart)

**What to build:** จุดเข้าเดียวสำหรับผู้ใช้ — ส่งข้อความภาษาไทย/อังกฤษ `POST /api/query {text}` → agent (rule + tools) ออกแบบแผน → คืน `{reply, data_points[], layers[], chart?, error}` จบในครั้งเดียว เหมือน "สั่งแชทแล้วได้แผนที่/กราฟ"

**Blocked by:** 03, 14, 15, 16

**Status:** ready-for-agent

- [ ] route `POST /api/query` → เรียก `Agent.handle()` ใหม่ (รองรับ data_points/layer/chart)
- [ ] schema response ครบ; จัดการ error/ไม่รู้คำสั่ง
- [ ] acceptance E2E: "จุดไฟในเชียงใหม่ กับอุณหภูมิวันนั้น สัมพันธ์กันไหม" → layer จุดไฟ + chart correlation