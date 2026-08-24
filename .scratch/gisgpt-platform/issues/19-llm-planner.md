# 19 — LLMPlanner (HF) สำหรับคำสั่งซับซ้อน

**What to build:** ให้สมอง LLM จริง (HuggingFace Inference API/fine-tune) เข้ามาช่วย เมื่อคำสั่งซับซ้อนเกิน rule-based — รับ NL → ตัดสินใจเลือก tools/params ถูกต้อง (hybrid: LLM ก่อน ถอย rule ถ้าไม่มี token)

**Blocked by:** 18

**Status:** ready-for-agent

- [ ] ต่อ LLMPlanner เข้ากับ `/api/query` (ใช้ HF_TOKEN ถ้ามี)
- [ ] prompt/JSON schema สำหรับ tool call
- [ ] เทสต์กรณี "เชียงใหม่ข้าวโพดหรือกาแฟ" กับ "จุดไฟกับฝุ่นสัมพันธ์ไหม" ทั้งโหมด rule มารอง LLM