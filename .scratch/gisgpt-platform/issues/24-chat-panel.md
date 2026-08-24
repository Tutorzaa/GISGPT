# 24 — Chat panel → /api/query

**What to build:** แผงแชทบนหน้าเว็บที่ผู้ใช้พิมพ์ภาษาไทย/อังกฤษ แล้วส่ง `POST /api/query` → วาดผลที่ได้ (ข้อความ + data points + layer) ลงบนแผนที่ทันที

**Blocked by:** 18, 23

**Status:** ready-for-agent

- [ ] input ช่องแชท + ประวัติข้อความ
- [ ] รับ response → วางจุด/data points + โชว์ layer บนแผนที่
- [ ] แสดง error/ข้อความผู้ช่วยอย่างชัด