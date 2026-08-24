# 17 — Agent tool: terrain + crop

**What to build:** ให้แชทบอทตอบโจทย์เชิงพื้นที่/การเกษตร — "อันดับภูเขา", "ข้าวโพด vs กาแฟ" → tool ต่อกับ elevation ranking (12) และ crop/landcover (13) แล้วตอบเป็นจุด/ชั้นภาพ

**Blocked by:** 03, 12, 13

**Status:** ready-for-agent

- [ ] tool `terrain_query(area)` → อันดับยอดเขา + จุด
- [ ] tool `crop_query(area, crop_a, crop_b)` → เปรียบเทียบ + evidence
- [ ] planner keyword: ภูเขา/ยอด/อันดับ/ข้าวโพด/กาแฟ/เพาะปลูก …