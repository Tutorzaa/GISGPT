# 16 — Agent tool: correlation

**What to build:** ให้แชทบอทรัน "พิสูจน์" ได้เอง — เมื่อถามว่า "จุดไฟกับอุณหภูมิสัมพันธ์กันไหม" → tool เดิน `/api/correlation` ระหว่าง metric ดาวเทียม↔met แล้วตอบผล + ส่ง scatter/graph เป็น chart

**Blocked by:** 03, 09

**Status:** ready-for-agent

- [ ] tool `correlation(metric_a, metric_b, area, time)` → `{r, p, n, chart, summary}`
- [ ] planner keyword: สัมพันธ์/ตรงไหม/พิสูจน์/related/correlate …
- [ ] pytest: ตัวอย่างได้ r/p + chart คืนให้ chat