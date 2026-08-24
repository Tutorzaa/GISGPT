# 01 — วางโครง backend + schema แถวมาตรฐาน + cache

**What to build:** โครงแพ็กเกจ backend สำหรับแพลตฟอร์ม (datasources / analysis / api / agent / benchmark) พร้อม schema `NormalizedRow` กลาง `{lat, lon, time, metric, value, src}` ที่ทุก adapter (ดาวเทียม & met) ต้องแปลงออกมาเป็นแบบเดียวกัน และชั้น cache แบบง่าย (JSON/SQLite) สำหรับผล fetch

**Blocked by:** None — เริ่มได้เลย

**Status:** ready-for-agent

- [ ] สร้างโครงแพ็กเกจตาม `docs/BACKEND_STRUCTURE.md` (หรือย้าย/จัด folder เดิมให้ตรง)
- [ ] กำหนด `NormalizedRow` (dataclass/pydantic) + ฟังก์ชัน normalize ทั่วไป
- [ ] ชั้น cache (อ่าน/เขียนจาก key `src:metric:bbox:time`) ใช้กับทุก data adapter
- [ ] ไฟล์ config อ่าน `.env` (คีย์ API ต่าง ๆ)
- [ ] pytest ครอบหน่วย schema + cache