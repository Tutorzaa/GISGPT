# 08 — Correlation engine (normative row → r/p + scatter)

**What to build:** เครื่องมือวิเคราะห์ความสัมพันธ์ 2 metric จากชุด NormalizedRow — ทั้งเชิงพื้นที่ (cross-sectional: ตามจุด) และเชิงเวลา (time-series: ตามวัน จับคู่ lag) — คืน Pearson r, p-value, n + ภาพ scatter PNG เพื่อ "พิสูจน์" ว่าดาวเทียมกับ met สัมพันธ์กันจริงหรือไม่ (reuse `geo/analysis.py`)

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] ฟังก์ชัน `correlate(rows_a, rows_b, mode, lag_days)` → `{r, p, n, method, scatter_png}`
- [ ] spatial join จับคู่จุดสองชุด (nearby + ช่วงวัน)
- [ ] จัดการ missing; รายงานข้อจำกัด (correlation ≠ causation)
- [ ] pytest จากข้อมูลจำลอง (บวก/ลบ/ไม่สัมพันธ์)