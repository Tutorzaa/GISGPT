# GISGPT Platform — Task Board (แผนย่อย ๆ + ทิศทาง)

> นี่คือ list ของงานย่อย (tickets) ที่แตกจากวิสัยทัศน์แพลตฟอร์ม
> (ดาวเทียม × สภาพอากาศ, สั่งผ่านแชทบอท AI, แสดง data point บนแผนที่ + กราฟ correlation เพื่อพิสูจน์ผล)
> ไฟล์ละ 1 งาน อยู่ใน `issues/NN-*.md` — แต่ละงานประกาศว่า "ต้องรออะไรก่อน" (blocked by)

## แผนผังทิศทาง (dependency graph — แนว Critical Path)

```
01 backend scaffold + schema
 └─ 02 geometry utils ─────────────────────────────────┐
     ├─ 04 GISTDA hotspot adapter                      │
     ├─ 05 NASA POWER adapter   ─┐                     │
     └─ 06 Open-Meteo adapter ──┼── 08 correlation engine
                                └── 07 /api/layers ── 09 /api/correlation
03 agent tool contract (map layer + chart) ──┐          │
     ├─ 14 agent met tool                    ├── 18 /api/query (NL→map)
     ├─ 15 agent satellite tool ─────────────┤     └── 19 LLM planner
     └─ 16 agent correlation tool ───────────┘
10 raster pixel layer ── 11 change layer ── 13 crop/landcover
12 elevation ranking
20 benchmark tasks → 21 runner → 22 /api/benchmark
23 web map shell ← (07,18,10)  → 24 chat panel · 25 chart · 26 raster on map
27 deploy
```

**วิธีอ่าน:** งานที่ "Blocked by: None" ทำได้เลย (frontier = 01, 03) → เมื่องานตัวล่างเสร็จ ตัวที่ถูกบล็อกก็ปลดล็อกเดินต่อ
**Critical path (ทางหลัก):** 01 → 02 → (04/05/06 → 08 → 09) และ 03 → (14/15/16) → 18 → 23 → 27
**มิติเนื้อหา (axis):** ดาต้า (04–06) → วิเคราะห์ (08–13) → agent (03,14–19) → API (07,09,18) → benchmark (20–22) → frontend (23–26) → deploy (27)

## เลเยอร์ที่งานแต่ละชิ้นตัดผ่าน (vertical-ish)
- **Proof-of-chain แนวตั้งชิ้นแรก:** 09 (`/api/correlation` hotspot↔PM2.5/อุณหภูมิ) = พิสูจน์ดาวเทียม↔met ด้วย API ตรง — ลำดับนี้เป็นจุดที่ทำเสร็จแล้วเป็นชิ้นใช้ได้จริงเร็วสุด
- **ผู้ใช้งานคนแรก:** 18 (`/api/query` ภาษาไทย → data point + layer + chart)

## หมายเหตุ
- 01–13 = backend core · 14–19 = agent/สมอง · 20–22 = วิจัย/benchmark · 23–27 = frontend+deploy (ทำต่อเมื่อ backend มั่นคง)
- status เริ่มต้นทุกงาน = `ready-for-agent`