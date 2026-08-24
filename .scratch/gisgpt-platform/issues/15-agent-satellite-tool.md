# 15 — Agent tool: satellite_query / hotspot

**What to build:** ให้แชทบอทเข้าใจคำขอที่อิงข้อมูลดาวเทียม (จุดไฟ, hotspot, การเผา) ตามจังหวัด/ขอบเขต → เรียก adapter GISTDA hotspot แล้วตอบ + ส่งจุดลงบนแผนที่ (extend planner keyword + registry)

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] tool `satellite_query(province, metric:"hotspot")` → `{rows, layer, top, text}`
- [ ] planner keyword: จุดไฟ/เผา/hotspot/ดาวเทียม … (มีแล้วบางส่วนใน `fire_hotspots`)
- [ ] pytest: คิวรีไทย → ได้ layer จุด hotspot + อันดับ