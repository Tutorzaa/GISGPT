# 03 — ขยายสัญญา tool ของ agent ให้รองรับ map layer + chart

**What to build:** ทำให้ agent tool กลับผลลัพธ์แบบใหม่ได้ นอกเหนือจาก `{text, artifacts, legend}` เดิม — เพิ่ม `data_points[]` (จุดบนแผนที่), `layer` (ชั้นภาพ/โพลิกอน), `chart` (ข้อมูลกราฟ correlations) เพื่อให้เมื่อพิมพ์ภาษาธรรมชาติ ระบบส่งข้อมูลสำหรับวาดแผนที่/กราฟกลับมาได้จริง

**Blocked by:** None — ต่อจาก `agent/` ที่มีอยู่

**Status:** ready-for-agent

- [ ] ขยาย `_compose` ใน `Agent` รวม `data_points/layer/chart` เข้า response
- [ ] schema `ToolResult` รองรับ field ใหม่ (ไม่ทำลาย field เดิม)
- [ ] pytest: tool ตัวอย่างคืน layer+chart แล้ว `handle()` รวมครบ