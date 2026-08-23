# 🖥️ Dashboard "Fire Emissions Watch" + AI Agent — วิธีทำ/กระบวนการ (Prototype)

> เป้าหมาย: เว็บแอพสไตล์ [CAMS Fire Emissions Watch](https://apps.atmosphere.copernicus.eu/fire-emissions-watch/)
> (แผนที่จุดไฟ + แผงกราฟวิเคราะห์ซ้าย) **บวก AI agent chatbot** ที่ตอบคำถาม GIS เป็นภาษาไทย
> ต่อยอดจากข้อมูล hotspot/ฝุ่นที่ทำไว้ใน Phase A–B

---

## 1. เป้าหมายสุดท้าย

```
┌───────────────────────────────────────────────────────────────┐
│ 🔥 GISGPT Fire Emissions Watch        [ภูมิภาค] [วันที่] [แสดง] │
├───────────┬────────────────────────────────────┬──────────────┤
│ แผงกราฟ   │                                    │ 💬 AI Agent  │
│ (ซ้าย)    │           แผนที่ (Leaflet)          │  แชทถามตอบ  │
│ • สรุป    │   จุดไฟสีตาม FRP + ขอบเขตจังหวัด    │  เป็นภาษาไทย │
│ • FRP/วัน │                                    │              │
│ • แยกจังหวัด│                                   │              │
└───────────┴────────────────────────────────────┴──────────────┘
```

**สไตล์อ้างอิง (Fire Emissions Watch):** MapLibre + deck.gl + ECharts, ธีมเขียวเข้ม `#0F4A57`,
ตัวเลือกช่วงวันที่ (d1–d2) — เราจำลองด้วย **Leaflet + ECharts + ธีมเดียวกัน** (เบากว่า, รันฟรี)

---

## 2. สถาปัตยกรรม (3 ชั้น)

| ชั้น | เทคโนโลยี | ไฟล์ |
|---|---|---|
| **Frontend** | Leaflet (แผนที่) + ECharts (กราฟ) + HTML/CSS/JS | `templates/dashboard.html`, `static/js/dashboard.js`, `static/css/dashboard.css` |
| **Backend** | Flask + geo modules (rasterio/shapely/requests) | `main.py`, `geo/dashboard.py`, `geo/hotspots.py`, `geo/airquality.py` |
| **AI Agent** | hybrid planner (rule + LLM) + tool registry | `agent/` |

### การไหลของข้อมูล

```
ผู้ใช้เลือกภูมิภาค+ช่วงวันที่ (หรือถามในแชท)
   │
   ▼
GET /api/dashboard?province=บุรีรัมย์&start=..&end=..
   │
   ▼  geo/dashboard.py
1. ขอบเขตจังหวัด (GeoJSON 77 จังหวัด) → bbox
2. FIRMS archive รายวัน (VIIRS/MODIS SP) → จุดไฟ {lat,lon,frp,date}
3. aggregate รายวัน + สรุป + แยกจังหวัด (shapely point-in-polygon)
   │
   ▼  JSON
Frontend: Leaflet วาดจุดสีตาม FRP · ECharts วาดกราฟ · AI agent ตอบคำถาม
```

### AI Agent ผูกกับ GIS ยังไง

- **Planner** (`agent/planner.py`) ตีความเจตนาจากคำถามภาษาไทย (เผา/ไฟ/ฝุ่น/สถิติ...)
- **Tools** (`agent/tools.py`) เป็น "แขน" ของ AI: `fire_hotspots`, `classify`, `stats`, `export`...
- AI แค่**ตัดสินใจว่าต้องเรียก tool อะไร** แล้ว tool ไปดึงข้อมูลจริง → คืนข้อความ+แผนที่/กราฟ
- ถ้าตั้ง `HF_TOKEN` → เปลี่ยนสมองเป็น LLM จริง (Qwen ผ่าน HF Inference API) เข้าใจคำถามซับซ้อนขึ้น

---

## 3. ข้อมูล (ฟรีทั้งหมด)

| ข้อมูล | แหล่ง | ใช้ทำอะไร |
|---|---|---|
| จุดความร้อน (hotspot) | NASA FIRMS (VIIRS/MODIS SP) + GISTDA | จุดไฟ + FRP (ความรุนแรง) |
| ขอบเขตจังหวัด | apisit/thailand.json (GeoJSON 77 จังหวัด) | วาดขอบเขต + กรองจุด |
| ฝุ่น PM2.5 | CAMS EAC4 (reanalysis) + GISTDA | กราฟยืนยันฝุ่น ↔ ไฟ |
| ภาพดาวเทียม | Copernicus Data Space (Sentinel-2) | (Phase C) การเปลี่ยนแปลงพื้นที่ |

---

## 4. กระบวนการทำ (ที่ทำแล้ว + จะทำต่อ)

| ขั้น | เนื้อหา | สถานะ |
|---|---|---|
| A | แผนที่ hotspot + ขอบเขตจังหวัด + จัดอันดับ | ✅ |
| B | ยืนยันด้วยฝุ่น/อุณหภูมิ (correlation) | ✅ |
| **E. Dashboard** | แผงกราฟวิเคราะห์ + แผนที่ + แชท AI (สไตล์ Fire Watch) | ✅ โปรโตไทป์ |
| C | การเปลี่ยนแปลงพื้นที่สีเขียว/เมือง (S2 2 ยุค) | ⏳ |
| D | เลือกพื้นที่จากแผนที่ (ROI) + deploy + LLM planner | ⏳ |

---

## 5. วิธีรันโปรโตไทป์

```bash
python main.py
# เปิด http://localhost:5000/dashboard
```

- เลือกจังหวัด + ช่วงวันที่ → กด **แสดง**
- ดูกราฟ: FRP รายวัน (เส้น) + จำนวนจุด (แท่ง) + แยกจังหวัด (แท่งแนวนอน)
- กด **💬 AI Agent** → ถาม เช่น *"จุดไหนเผาเยอะสุด"*, *"สรุปสถานการณ์ไฟ"*

---

## 6. ข้อจำกัดปัจจุบัน (ต้องพูดถึง)

- FIRMS SP มีดีเลย์ ~7–10 วัน → ข้อมูล "ล่าสุด" ใช้ NRT แทน (เพิ่มได้)
- สี/สเกล FRP เป็นค่าตั้งเอง (ยังไม่ normalize ตาม GFAS)
- จุดใน bbox ที่ติดชายแดน (กัมพูชา) จะขึ้นเป็น "(นอกไทย/ทะเล)" — ต้องกรอง polygon 77 จังหวัดให้ครบหรือตัดชายแดน
- กราฟยัง static — ต่อไปให้แชทสั่งเปลี่ยนกราฟ/ช่วงเวลาได้ (agent ↔ dashboard สองทาง)

---

## 7. Roadmap ต่อ (ระยะสั้น)

1. แชท AI **สั่ง dashboard ได้** (เช่น "แสดงเฉพาะวันพีค" → กราฟ/แผนที่เปลี่ยน)
2. เพิ่ม FIRMS NRT (ข้อมูลสด 7 วัน) + สลับ SP/NRT อัตโนมัติ
3. กราฟ PM2.5 (CAMS) เทียบ FRP ใน panel เดียวกัน
4. ROI เลือกพื้นที่จากแผนที่ → dashboard อัปเดตเฉพาะพื้นที่
5. Deploy HF Spaces (Gradio/Flask) + landing Vercel
