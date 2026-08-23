# GISGPT 🌍 — Geospatial Foundation Model Agent

**GISGPT** คือ AI chatbot ด้านภูมิสารสนเทศ ที่รวม **ภาพถ่ายดาวเทียม (Satellite Imagery) + GIS + AI Foundation Model**
ผู้ใช้เลือกพื้นที่บนแผนที่ / อัปโหลดภาพดาวเทียม แล้วถามคำถามภาษาธรรมชาติ (ไทย/อังกฤษ)
ระบบตอบกลับด้วย **ข้อมูลเชิงพื้นที่ที่มองเห็นได้** เช่น การจำแนก land cover (ป่า/น้ำ/เมือง/เกษตร), ดัชนีสเปกตรัม, สถิติพื้นที่

โปรเจกต์มี **2 ส่วนหลัก** ที่ทำงานเสริมกัน:

| ส่วน | เทคโนโลยี | หน้าที่ |
|---|---|---|
| **Agent app** (ใหม่) | Python + Flask + ONNX | สมอง AI: รับคำสั่งแชท → วิเคราะห์ภาพดาวเทียม → ตอบผล + แผนที่ผลลัพธ์ |
| **Web GIS platform** | OpenLayers (JavaScript) | จัดการแผนที่/เลเยอร์, นำเข้าไฟล์ GeoJSON/Shapefile/KML/GPX — เส้นทางสู่ GIS app เต็มรูปแบบ |

---

## โครงสร้าง Repository

```
GISGPT/
├── main.py                  ← Flask agent app (entry point: python main.py)
├── agent/                   ← สมองของ agent (hybrid planner + tool registry)
│   ├── planner.py           — ตีความคำสั่งภาษาไทย/อังกฤษ (rule-based)
│   ├── llm.py               — สมอง LLM ตัวที่สอง (HF Inference API, สลับได้เมื่อมี token)
│   ├── registry.py          — ลงทะเบียนเครื่องมือ (tools)
│   ├── tools.py             — ตัวเครื่องมือ: จำแนก / ดัชนี / สถิติ / อธิบาย / export
│   └── memory.py            — หน่วยความจำต่อ session
├── geo/                     ← GIS pipeline (Python)
│   ├── io.py                — อ่าน/เขียน GeoTIFF (rasterio)
│   ├── tiling.py            — ตัดภาพเป็น patch 224×224 + ปะกลับ (sliding window)
│   ├── indices.py           — NDVI / NDWI / NDBI + ตัวจำแนก baseline
│   ├── landcover.py         — รันโมเดล ONNX (Prithvi head) บน CPU
│   ├── pipeline.py          — รวมขั้นตอนวิเคราะห์ให้ agent เรียกใช้
│   └── visualize.py         — ระบายสี class map, สถิติพื้นที่, PNG
├── scripts/
│   ├── finetune.py          — Fine-tune Prithvi-EO-2.0-300M → ONNX → push HF
│   ├── make_test_tiff.py    — สร้างภาพจำลองสำหรับเทสต์
│   └── fetch_sample_data.py — ดาวน์โหลดภาพตัวอย่าง (best-effort)
├── notebooks/
│   ├── 01-intro-satellite-analysis.ipynb   ← learning path เดิม
│   ├── 02-gistda-open-data.ipynb           ← learning path เดิม
│   ├── 03-explore-prithvi-mae.ipynb        ← เล่น MAE reconstruction กับ Prithvi จริงบน CPU
│   └── 04-finetune-landcover-colab.ipynb   ← Fine-tune land cover บน Colab (GPU)
├── platform/                ← Web GIS platform (OpenLayers) — ส่วนเดิม
├── prototype/               ← Web prototype เดิม (Leaflet chat demo)
├── templates/ + static/     ← UI ของ Flask agent app
├── docs/
│   ├── DEV_LOG.md           ← บันทึกการพัฒนาทุกครั้ง (หลักฐาน)
│   ├── satellite-data.md    ← แหล่งข้อมูลดาวเทียมฟรี (อัปเดตล่าสุด)
│   ├── gistda-data.md       ← คู่มือ GISTDA Open Data API
│   └── PROTOTYPE.md         ← รายละเอียด prototype เดิม
└── requirements.txt
```

> ไฟล์ใหญ่ (ข้อมูล/โมเดล/ผลลัพธ์) อยู่ใน `.gitignore` — ไม่ push ขึ้น GitHub

---

## Quick Start

### 1) Agent app (Flask) — ตัวใหม่

```bash
pip install -r requirements.txt
python main.py
# เปิด http://localhost:5000
```

- ลากไฟล์ **GeoTIFF** (Sentinel-2/Landsat/HLS) มาวางในแชท
- พิมพ์คำสั่ง เช่น `จำแนก land cover`, `คำนวณ NDVI`, `สถิติพื้นที่`, `export`
- ระบบจะตอบกลับด้วย **แผนที่ผลลัพธ์ (PNG) + สถิติพื้นที่ (เฮกตาร์/ตร.กม.) + legend คลาส**

ไม่มีภาพจริง? รัน `python scripts/make_test_tiff.py` เพื่อสร้างภาพจำลองทดสอบก่อน

### 2) Web GIS platform — ส่วนเดิม

เปิด `platform/index.html` ใน browser (ไม่ต้องติดตั้ง) — จัดการเลเยอร์, นำเข้าไฟล์, ดูตาราง attribute

---

## ระบบ Agent ทำงานยังไง

```
ผู้ใช้พิมพ์คำสั่ง (ไทย/อังกฤษ)
        │
        ▼
┌───────────────── agent/planner.py ─────────────────┐
│ ตีความเจตนา (intent) จากคีย์เวิร์ด:                │
│ จำแนก → classify · NDVI → index · พื้นที่ → stats │
│ (ถ้ามี HF_TOKEN: สลับใช้ LLMPlanner ผ่าน            │
│  Hugging Face Inference API อัตโนมัติ — hybrid)     │
└────────────────────────┬───────────────────────────┘
                         ▼
               agent/registry.py (tools)
   classify │ index │ stats │ explain │ export │ help
                         ▼
┌───────────────── geo/pipeline.py ──────────────────┐
│ 1. rasterio อ่าน GeoTIFF → reflectance 0–1        │
│ 2. tiling.py ตัดเป็น patch 224×224 (overlap 50%)  │
│ 3. landcover.py: ONNX (Prithvi head) → logits     │
│    (ไม่มีโมเดล → fallback เป็น NDVI/NDWI/NDBI)     │
│ 4. stitch รวม patch → class map เต็มภาพ            │
│ 5. visualize: ระบายสี + คำนวณพื้นที่จริง           │
└────────────────────────┬───────────────────────────┘
                         ▼
        ตอบกลับ: ข้อความ + แผนที่ PNG + สถิติ + legend
```

**สัญญาโมเดล ONNX** (ผลจาก `scripts/finetune.py`):
```
input : (1, 1, 6, 224, 224) float32 — reflectance 0–1, 6 แบนด์
output: (1, num_classes, 224, 224) logits ต่อพิกเซล (semantic segmentation)
```

> ⚠️ ลำดับแบนด์ 6 ช่องต้องตรงกับโมเดล: **Prithvi-EO-2.0 ฝึกด้วย B02–B07** (น้ำเงิน→เรดเอจ)
> ภาพที่อัปโหลดควรเลือกแบนด์ลำดับนี้ (ดู `geo/landcover.py`)

---

## Geospatial Foundation Model: Prithvi-EO-2.0 (NASA–IBM)

- โมเดล 330 ล้านพารามิเตอร์ ฝึกแบบ **MAE (Masked Autoencoder)** ด้วยภาพ HLS 4.2 ล้านชุดทั่วโลก — ไม่ต้องใช้ label
- **เช็คสิทธิ์/ดาวน์โหลด:** เปิดฟรี (Apache-2.0, ไม่ gated) — `hf auth login` แล้ว
  `hf download ibm-nasa-geospatial/Prithvi-EO-2.0-300M Prithvi_EO_V2_300M.pt --local-dir models/pretrained`
- **เล่นบน CPU ได้จริง** (notebook 03): MAE ปิด 75% ของภาพแล้วให้โมเดลสร้างใหม่ — ~1.1 นาที/ชุด 4 เฟรม
- **Fine-tune → ใช้ในแอป** (notebook 04 บน Colab GPU):
  1. โหลด Sen4Map (land cover 10 คลาส) → ตัดเฟรมแรก + 6 แบนด์ B02–B07
  2. `scripts/finetune.py` เทรน UPerNet head → export ONNX
  3. push ขึ้น HF → วาง `.onnx` + `_classes.json` ใน `models/` → แอปสลับใช้โมเดลอัตโนมัติ

---

## ผลการทดสอบ (สรุป)

| รายการ | ผล |
|---|---|
| pipeline baseline (NDVI/NDWI/NDBI) + สถิติพื้นที่ | ✅ ผ่าน — ภาพจำลอง + ภาพจริง HLS Mexico |
| agent rule-based 7 เครื่องมือ (ไทย/อังกฤษ) | ✅ ผ่านทุก intent |
| Flask: upload → chat → แสดงผล → export GeoTIFF | ✅ ผ่าน (test client, HTTP 200) |
| MAE reconstruction Prithvi-EO-2.0 จริงบน CPU | ✅ ผ่าน — 1.1 นาที/ชุด 4 เฟรม |
| finetune.py เทรน + export ONNX (สัญญา 1,1,6,224,224) | ✅ ผ่าน — terratorch 1.2.x (`PrithviModelFactory().build_model`, `ckpt_path=`, `UperNetDecoder`) |

ดูรายละเอียดเต็มใน `docs/DEV_LOG.md`

---

## แหล่งข้อมูลดาวเทียม

อัปเดตล่าสุดใน **[docs/satellite-data.md](docs/satellite-data.md)** — สรุปสั้นๆ:

- **Copernicus Data Space (Sentinel-2 L2A)** — ฟรี 10 ม. สมัครที่ dataspace.copernicus.eu — ใช้ **STAC API** (รุ่น Open Access Hub ถูกปิดแล้ว)
- **GISTDA** — NSDC (nsdc.gistda.or.th) + API Gateway (พื้นที่ปลูกข้าว/น้ำท่วม/ภาพ 2 เมตร) ดู [docs/gistda-data.md](docs/gistda-data.md)
- **NASA** — GIBS (ภาพแผนที่พื้นหลัง ไม่ต้อง login), POWER (สภาพอากาศ/เกษตร), CMR/Earthdata (ค้นหา metadata)

---

## Roadmap

> 🚜 ระบบเฝ้าระวังการเผาไร่เผานา (hotspot + ฝุ่น PM2.5 + ขอบเขตจังหวัดบุรีรัมย์) — แผนเต็มใน **[docs/BURN_MONITORING_PLAN.md](docs/BURN_MONITORING_PLAN.md)**

- [ ] **Phase A** แผนที่ hotspot บุรีรัมย์ + ขอบเขตจังหวัด + จัดอันดับ FRP (GISTDA + NASA FIRMS)
- [ ] **Phase B** ยืนยันข้ามข้อมูล: hotspot ↔ ฝุ่น/อุณหภูมิ GISTDA (correlation)
- [ ] **Phase C** การเปลี่ยนแปลงพื้นที่สีเขียว / เมืองขยาย (Sentinel-2 2 ช่วงเวลา)
- [ ] **Phase D** เลือกพื้นที่จากแผนที่ (ROI) + ผูกกับแชท agent + deploy HF Spaces
- [ ] ดึงข้อมูล Sentinel-2 ผ่าน **Copernicus STAC API** — สั่งแชทเป็นพื้นที่/พิกัดได้
- [ ] Fine-tune Prithvi จริงบน Colab → ใช้โมเดล land cover จริงในแอป
- [ ] เปิดใช้สมอง LLM (`HF_TOKEN`) ให้เข้าใจคำสั่งซับซ้อนขึ้น
- [ ] แผนที่พื้นหลัง NASA GIBS ใน UI

---

## หมายเหตุ

- โปรเจกต์พัฒนาบน Windows 11 + conda env `ml` (Python 3.11) — ดู `docs/DEV_LOG.md` สำหรับรายละเอียดการพัฒนา
- คอนโซล Windows (cp1252) อ่านภาษาไทยไม่ได้ → รันด้วย `PYTHONIOENCODING=utf-8`
