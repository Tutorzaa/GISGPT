# 14 — Agent tool: met_query

**What to build:** ให้แชทบอทเข้าใจคำขอสภาพอากาศ (กว้าง/จุด/ช่วงเวลา "อุณหภูมิวันนั้นเป็นเท่าไหร่") → เรียก adapter met (NASA POWER/Open-Meteo) และตอบ + ส่ง layer ไปวาดบนแผนที่ (extend planner keyword + registry)

**Blocked by:** 03, 06

**Status:** ready-for-agent

- [ ] tool `met_query(area, metric, time)` → `{rows, layer, text}`
- [ ] planner keyword: อุณหภูมิ/ฝน/ลม/สภาพอากาศ/weather …
- [ ] pytest: คิวรีภาษาไทย → ได้ layer met