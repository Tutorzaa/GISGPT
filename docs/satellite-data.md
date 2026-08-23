# แหล่งข้อมูลภาพถ่ายดาวเทียม (ฟรี) — อัปเดตล่าสุด

คำแนะนำแหล่งดาวน์โหลดภาพถ่ายดาวเทียมสำหรับฝึกวิเคราะห์และใช้ใน GISGPT
(รวมสถานะ API ณ ปี 2025–2026 และเส้นทางที่เหมาะกับโมเดล Prithvi)

---

## 1. Sentinel-2 — Copernicus Data Space Ecosystem ⭐ (แนะนำ)

- **ความละเอียด:** 10 เมตร (B2, B3, B4, B8) / 20 เมตร (B5–B7, B11, B12)
- **ความถี่:** ทุก ~5 วัน ครอบคลุมทั้งโลก รวมถึงประเทศไทย
- **ราคา:** ฟรี 100%
- **สมัคร:** https://dataspace.copernicus.eu (ฟรี)

### วิธีดาวน์โหลด (หน้าเว็บ)

1. เข้า [Copernicus Browser](https://browser.dataspace.copernicus.eu/)
2. เลือกพื้นที่/ช่วงวันที่ → กรอง `Sentinel-2` → เลือกภาพเมฆน้อย (Cloud cover)
3. ดาวน์โหลดแบบ **L2A (Surface Reflectance)** → เลือก band ที่ต้องการ
4. ได้ไฟล์ GeoTIFF นำไปใช้กับแอป/notebook ได้เลย

### API (สำหรับ agent ของเรา — วางแผนไว้)

⚠️ **Copernicus Open Access Hub (scihub) ถูกปิดไปแล้ว** — API ปัจจุบัน:

| API | จุดเข้าถึง | ใช้ทำอะไร |
|---|---|---|
| **STAC Catalogue** (ใหม่, STAC 1.1.0) | `https://catalogue.dataspace.copernicus.eu/stac` | ค้นหาภาพตาม bbox/วันที่/เมฆ — เหมาะกับ agent |
| OData | `https://catalogue.dataspace.copernicus.eu/odata/v1` | ค้นหาแบบเก่า (ยังใช้ได้) |
| Process API | `https://sh.dataspace.copernicus.eu/api/v1/process` | ดึงข้อมูลโดยตรง |

**หมายเหตุสำหรับโมเดล GISGPT:** Prithvi-EO-2.0 ฝึกด้วยแบนด์ **B02–B07** (น้ำเงิน→เรดเอจ)
ถ้าจะป้อนเข้าโมเดล ต้องเลือก band ชุดนี้โดยเฉพาะ (ไม่ใช่ B08 NIR)

---

## 2. GISTDA (ไทย) — NSDC + API Gateway

- **NSDC (National Space Data Platform):** https://nsdc.gistda.or.th — แพลตฟอร์มข้อมูลอวกาศแห่งชาติ
  มี **THEOS-2** (ดาวเทียมไทย ความละเอียด ~0.5 ม. pan) และข้อมูล Copernicus
- **API Gateway:** https://api-gateway.gistda.or.th — สมัครคีย์ฟรี ใช้ดึง พื้นที่ปลูกข้าว/น้ำท่วม/ภาพ 2 เมตร
- ดูคู่มือเต็มใน **[docs/gistda-data.md](gistda-data.md)**

---

## 3. NASA — 3 API ที่ใช้ได้จริง

| API | ต้องสมัคร? | ใช้ทำอะไร |
|---|---|---|
| **GIBS** (`https://gibs.earthdata.nasa.gov`) | ❌ ไม่ต้อง | ภาพดาวเทียมสำเร็จรูป (MODIS ฯลฯ) เป็นแผนที่พื้นหลัง — WMTS tile ใช้กับ Leaflet/OpenLayers ได้ทันที |
| **POWER** (`https://power.larc.nasa.gov`) | ❌ ไม่ต้อง | สภาพอากาศ/พลังงานแสงอาทิตย์ (อุณหภูมิ, รังสี) — ต่อยอดงานเกษตร |
| **CMR / Earthdata** (`https://cmr.earthdata.nasa.gov`) | ✅ Earthdata login | ค้นหา metadata ข้อมูล Earth science ทั้งหมด + ดาวน์โหลด |

### Landsat 8/9 — NASA/USGS

- 30 เมตร ทุก 16 วัน ข้อมูลย้อนหลังตั้งแต่ปี 1984 — เหมาะศึกษาการเปลี่ยนแปลง
- [USGS EarthExplorer](https://earthexplorer.usgs.gov/) (สมัครฟรี) — ใช้ Collection 2 Level-2
- หรือ **USGS M2M API** (Machine-to-Machine) สำหรับดึงอัตโนมัติ

---

## 4. ทางเลือกอื่น

- **Google Earth Engine (GEE)** — ประมวลผลบน cloud ไม่ต้องดาวน์โหลด เหมาะหลายพื้นที่/หลายช่วงเวลา (code.earthengine.google.com)
- **Microsoft Planetary Computer** — STAC API สำหรับ Sentinel-2/Landsat + หลายชุดข้อมูล (planetarycomputer.microsoft.com)
- **HLS (Harmonized Landsat Sentinel)** — ข้อมูลที่ Prithvi ฝึกด้วย (30 ม., 6 แบนด์) — ดาวน์โหลดจาก NASA Earthdata

---

## สรุปเส้นทางแนะนำ (อัปเดต)

| ขั้น | เครื่องมือ | ใช้ทำอะไร |
|---|---|---|
| 1. เรียนรู้ | Sentinel-2 + notebook 01/02 | ฝึกอ่านภาพ คำนวณ NDVI/NDWI |
| 2. เล่นกับโมเดล | notebook 03 | MAE reconstruction — ดู Prithvi "เห็น" อะไร |
| 3. เทรนโมเดล | notebook 04 (Colab GPU) | Fine-tune Prithvi → land cover → ONNX |
| 4. ใช้ในแอป | Flask agent app | อัปโหลดภาพ → จำแนก → สถิติพื้นที่ |
| 5. (เร็วๆ นี้) ดึงอัตโนมัติ | Copernicus STAC API | สั่งแชทเป็นพื้นที่ → agent ดึง Sentinel-2 ให้เอง |
