# 23 — Web map shell + layer switcher (แบบ Windy)

**What to build:** โครงหน้าจอเว็บพื้นฐานที่ผู้ใช้เปิดเบราว์เซอร์แล้วเห็นแผนที่ + ปุ่มสลับ/ซ้อนชั้นภาพ (satellite basemap, hotspot, อุณหภูมิ, ฝุ่น, พิกเซลสี land cover) — รองรับ bounce ตะวันออก/ดึงคุ้มเมื่อ backend API (07,18) พร้อม

**Blocked by:** 07, 18, 10

**Status:** ready-for-agent

- [ ] Leaflet map + basemap (GIBS/OSM) + layer switcher UI
- [ ] โหลด layer จาก `/api/layers/<name>` ลงแผนที่
- [ ] responsive มือถือ/เดสก์ท็อป + เลเยอร์ซ่อน/แสดง