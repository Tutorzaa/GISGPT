# GISGPT — สถาปัตยกรรมแพลตฟอร์ม (Geospatial × Meteorological Fusion)

> สถานะ: **เอกสารออกแบบ (ยังไม่ลงโค้ด UI)** — โฟกัสโครง backend ก่อน
> จุดกำเนิด: ผู้ใช้ต้องการแพลตฟอร์มแผนที่แบบ Windy ที่ผสาน **ข้อมูลดาวเทียม + สภาพอากาศ** ควบคุมผ่าน **แชทบอท AI (Geospatial Foundation Model)** โดยแสดงผลเป็น **data point บนแผนที่** + **กราฟความสัมพันธ์** เพื่อพิสูจน์ว่าการวิเคราะห์ถูกต้อง และใช้เป็นงานวิจัย/benchmark เชิงพื้นที่-เวลา

---

## 1. วิสัยทัศน์ และเป้าหมาย

**หนึ่งประโยค:** แพลตฟอร์มที่ใช้ Geospatial Foundation Model (GFM) วิเคราะห์ข้อมูลดาวเทียม เปรียบเทียบกับข้อมูลสภาพอากาศ (meteorological) แล้วแสดงผลเป็นจุด/ชั้นภาพบนแผนที่โลก + กราฟความสัมพันธ์ — สั่งผ่านภาษาธรรมชาติในแชทบอท

**หลักการออกแบบ:**
1. **ข้อมูล 2 โคแกนต์** — ระบบ GIS (ภาพดาวเทียม) ↔ ระบบ met (สภาพอากาศ) ที่สัมพันธ์กันอย่างมีนัยสำคัญ
2. **สมอง = AI agent (chatbot)** — แปลภาษาธรรมชาติ → โค้ด/คำขอ → วิเคราะห์ → เอาต์พุตเป็น data point บนแผนที่ + กราฟ
3. **พิสูจน์ผล (evidence)** — แสดงความสัมพันธ์เชิงสถิติ (correlation) ระหว่างดาวเทียมกับ met ทุกครั้ง เพื่อ verify ว่าผลวิเคราะห์สมเหตุสมผล
4. **เลเยอร์เหมือน Windy** — สลับ/ซ้อนชั้นภาพ (satellite basemap, จุดไฟ, ฝุ่นความร้อน, อุณหภูมิ/ลม, พิกเซลสี land cover) ได้อิสระ

**ตัวอย่างโจทย์ที่ต้องรองรับ (จากผู้ใช้):**
- "ดู mountain rankings เรียงลำดับ" → เลือกจุดแต่ละลูกได้ในขอบเขต
- "เดือนนี้เชียงใหม่ ปลูกข้าวโพดหรือกาแฟมากกว่า" → crop/land cover เชิงพื้นที่-เวลา
- hotspot ↔ ฝุ่น/อุณหภูมิ (Buriram) → correlation
- การเปลี่ยนแปลงพื้นที่สีเขียว/เมือง ตามช่วงเวลา

**มุมวิจัย:**
- คำถามวิจัย: *เราใช้ AI (GFM) วิเคราะห์เพื่อ "ยืนยันเหตุการณ์" และ "verify ความเข้าใจของโมเดลจากข้อมูล" ได้ไหม?*
- ทดสอบ **benchmark** ของโมเดลในการวิเคราะห์ความสัมพันธ์ของภาพตามช่วงเวลา (spatio-temporal)
- เป้าหมายรอง: ให้โมเดลเรียนรู้วิเคราะห์ real-world data 2 ชนิดที่สัมพันธ์กัน (GIS + met)

---

## 2. สถาปัตยกรรมโดยรวม (ระบบ 4 ชั้น)

```
┌─ Layer 4 · Frontend (ทำหลัง backend เสร็จ) ──────────────┐
│  Web Map (Leaflet/MapLibre) + Layer Switcher (แบบ Windy) │
│  แชทบอท (side panel) + กราฟ ECharts + ตาราง/จุดบนแผนที่  │
└──────────────────────────┬───────────────────────────────┘
                           │ REST /api (JSON: layers, data_points, chart)
┌─ Layer 3 · Agent (สมอง, ผสาน NL→โค้ด) ──────────────────┐
│  พิมพ์ไทย/อังกฤษ → planner (rule + LLM/HF) → tools:      │
│  · met_query · satellite_query · elevation · crop_stat  │
│  · correlation · change_detect · hotspot               │
└──────────────────────────┬───────────────────────────────┘
┌─ Layer 2 · Analysis Engine ──────────────────────────────┐
│  GFM (Prithvi ONNX) land cover/change · indices         │
│  NDVI/NDWI/NDBI · Correlation (Pearson cross/time)      │
└──────────────────────────┬───────────────────────────────┘
┌─ Layer 1 · Data Adapters (normalize ทั้งหมดเป็นแถวเดี่ยว) ┐
│  Satellite: GISTDA, FIRMS, Copernicus STAC (S2/Landsat) │
│  Met: NASA POWER, CAMS EAC4, Open-Meteo, ERA5          │
│  Terrain: SRTM/GMTED (elevation → mountain ranking)    │
│  Unify → {lat, lon, time, metric, value, src}          │
└──────────────────────────┬───────────────────────────────┘
                           ▼
             Cache (JSON/SQLite) + Geometry utils
```

**แนวคิดสำคัญ — Normalized Row (แกนเชื่อมทุกอย่าง):**
ทุกแหล่งข้อมูล (ดาวเทียม และ met) ถูกปรับเป็นแถวมาตรฐานเดียวกัน:
```json
{ "lat": 18.9, "lon": 98.9, "time": "2023-04-05", "metric": "pm2p5_n", "value": 45.2, "src": "cams_eac4" }
{ "lat": 18.9, "lon": 98.9, "time": "2023-04-05", "metric": "hotspot_frp", "value": 84.0, "src": "firms" }
```
คราวนี้การ **spatial join / correlation / เปรียบเทียบตามเวลา** ทำได้บนชุดแถวเดียวกัน → ง่ายต่อ agent และ benchmark

---

## 3. Tech Stack (แนะนำ, อิงของเดิมที่ reuse ได้)

| ส่วน | เทคโนโลยี | หมายเหตุ |
|---|---|---|
| Backend | Python 3.11–3.13, **Flask** (reuse `main.py`) หรือ FastAPI | เก็บ Flask เพื่อ reuse agent/geo |
| คำนวณ raster | numpy, rasterio, opencv | มีแล้ว |
| GFM | Prithvi-EO-2.0-300M → **onnxruntime** | reuse `geo/landcover.py`, `scripts/finetune.py` |
| Met fusion | cdsapi/netCDF4 (CAMS), requests (NASA POWER / Open-Meteo) | บางส่วนมีแล้ว |
| Geo | shapely, geopandas, (s2geometry) | จุดในโพลี/บัฟเฟอร์ |
| Agent | reuse `agent/` (planner/registry/tools) | ขยาย tools สำหรับ met/satellite/terrain |
| Frontend (ภายหลัง) | Leaflet (หรือ MapLibre) + ECharts + vanilla JS | แบบ Windy; ไม่ทำตอนนี้ |

---

## 4. แผนงาน (แบ่งงานใหญ่เป็นชิ้น) — กลับลำดับตามวิสัยทัศน์จริง

### P0 — โครง backend + เอกสาร + 데이터 normalize (ตอนนี้)
- เอกสารสถาปัตยกรรม/โครงนี้ + backend module tree + API spec ✅
- วางโครงแพ็กเกจ `datasources/`, `analysis/`, `api/` พร้อม adapter normalize เป็นแถวเดียว
- เปิดเส้นข้อมูลฟรี (ไม่มีคีย์): GISTDA hotspot (ใช้ได้แล้ว), NASA POWER / Open-Meteo (met), GIBS basemap

### P1 — Proof-of-chain บน backend (API ตรง ไม่ต้อง UI)
- API: `POST /api/query` (NL) → agent → กลับ `data_points[] + chart + layer`
- API: `PROJECTION /api/correlation{metric_a, metric_b, bbox, time}` → r/p + scatter PNG
- เทสต์ห่วงโซ่จริง: hotspot (satellite) ↔ PM2.5/อุณหภูมิ (met) → correlation (ใช้ของเดิม `geo/analysis.py`)

### P2 — เลเยอร์ + GFM จริง + โจทย์เชิงพื้นที่
- Layer switcher ต้าน (แต่ยังหัวใจ backend): land cover/change raster → พิกเซลสีบนแผนที่
- crop/land cover เชิงเวลา → ตอบ "เชียงใหม่ ข้าวโพด vs กาแฟ"
- mountain ranking จาก SRTM

### P3 — วิจัย / benchmark
- ชุด benchmark spatio-temporal: event-regions ที่รู้ค่า → ทดสอบ GFM วิเคราะห์/verify
- เมตริก: r, p, R², RMSE, accuracy ของ detection; รายงานความเข้าใจโมเดล

### P4 — Frontend แบบ Windy + deploy
- Web map + layer switcher + แชท + กราฟ (ทำตามเอกสารนี้ตอน backend มั่นคง)
- Deploy: Docker → HF Spaces / Vercel + scheduler

---

## 5. API Design (เป้าหมาย backend)

```
POST /api/query            {text: "จุดไฟในเชียงใหม่ กับอุณหภูมิวันนั้น สัมพันธ์กันไหม"}
                           → agent วางแผน → {reply, data_points[], layers[], chart?, error?}
POST /api/correlation      {metric_a:"hotspot_frp", metric_b:"cams_pm25", bbox, start, end}
                           → {r, p, n, scatter_png, summary}
GET  /api/layers           → รายการ layer metadata (satellite/met/terrain) ที่มี
GET  /api/layers/<name>?bbox&time&res   → GeoJSON/data points
GET  /api/elevation        → จุดยอดสูงสุด (mountain ranking) ใน bbox จาก SRTM
GET  /api/benchmark        → คำอธิบาย/ผล benchmark spatio-temporal
POST /api/agent/register   → ลงทะเบียน tool ใหม่
```

> รายละเอียดเต็ม (พารามิเตอร์/response schema/ตัวอย่าง) อยู่ใน `docs/BACKEND_STRUCTURE.md`

---

## 6. คำถามค้าง / ต้องตัดสินใจ

1. **Backend framework:** Flask (ต่อ) vs FastAPI → แนะนำ Flask (reuse ของเดิม) แต่เปิดให้สอบได้
2. **ข้อมูล met หลัก:** NASA POWER (ฟรี ไม่มีคีย์) vs CAMS EAC4 (ต้องคีย์ ADS) vs Open-Meteo → ตอนนี้เริ่มฟรีๆ ก่อน
3. **GFM จริงตอนไหน:** ใช้ baseline (NDVI/NDBI) พิสูจน์ห่วงโซ่ก่อน แล้วแทรก Prithvi จริงเมื่อเทรน — เพื่อแยก "ปัญหากระบวนการ" ออกจาก "คุณภาพโมเดล"
4. **ขอบเขตโจทย์ "เชียงใหม่ ข้าวโพด vs กาแฟ":** ต้อง crop map (เช่น ESA WorldCover 10 ม., ฟรี) + อุณหภูมิ/ฝนตามฤดู → มั่นใจได้ว่าวิเคราะห์ถูกต้องแค่ไหน (data available)
5. **Storage:** เริ่ม JSON cache → upgrade SQLite เมื่อ data เยอะ

---

## 7. สรุป
- **เป้า:** แพลตฟอร์ม Windy-like ผสานดาวเทียม+met สั่งด้วยแชทบอท AI → data point + correlation proof → งานวิจัย/benchmark
- **ตอนนี้:** ทำโครง backend + เอกสาร (เอกสารนี้ + `BACKEND_STRUCTURE.md`) ยังไม่ทำ UI
- **ลำดับถัดไป:** P1 พิสูจน์ห่วงโซ่ด้วย API ตรง (satellite↔met correlation) โดยใช้ข้อมูลฟรี