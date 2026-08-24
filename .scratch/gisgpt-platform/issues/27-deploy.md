# 27 — Deploy (Docker → HF Spaces / สลับ hosting)

**What to build:** ให้แพลตฟอร์มรันได้ที่อื่นด้วย — Dockerfile ครอบ backend+frontend, พร้อมปุ่ม deploy ไป HuggingFace Spaces (gradio/flask) / Vercel — ผู้ใช้คนอื่นเข้าถึงผ่าน URL ได้

**Blocked by:** 18, 23

**Status:** ready-for-agent

- [ ] Dockerfile + docker-compose (backend + static + cache)
- [ ] ตั้ง env คีย์ (ไม่ commit คีย์); healthcheck
- [ ] คู่มือ deploy (HF Spaces + Vercel) + ทดสอบ build