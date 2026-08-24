# 09 — API: /api/correlation (hotspot ↔ met)

**What to build:** ผู้เรียกส่ง `{metric_a, metric_b, bbox, start, end}` เช่น hotspot_frp↔cams/nasa อุณหภูมิ แล้วได้ `{r, p, n, scatter_png, summary}` — ห่วงโซ่แรกที่พิสูจน์ "ดาวเทียม↔met" ด้วย API ตรง ใช้ได้จริง (เป็นชิ้นงานคุ้มสุดในระยะสั้น)

**Blocked by:** 08, 04, 05 (ต้องมีฝั่ง sat + met)

**Status:** ready-for-agent

- [ ] route `POST /api/correlation` + validation schema
- [ ] ต่อกับ adapter GISTDA hotspot + NASA POWER/Open-Meteo
- [ ] เอกสารตัวอย่าง curl + ผล real (ใช้ข้อมูล 2020-08-29 มีอยู่แล้ว)