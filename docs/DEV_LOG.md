# DEV_LOG — GISGPT (Geospatial Foundation Model Agent)

กฎ: ทุกครั้งที่แก้โค้ด ต้อง (1) ทดสอบผ่าน (2) เขียน log นี้ (3) commit

## 2026-08-23
- **เริ่มโปรเจกต์ GISGPT** — Geospatial Foundation Model Agent (จำแนก land cover ผ่าน web chat)
- สถาปัตยกรรม: Flask web app + agent hybrid (rule-based planner เป็นหลัก, สลับ LLM ผ่าน HF Inference API ได้) + GIS pipeline (rasterio/onnxruntime)
- โมเดลเป้าหมาย: Prithvi-EO-2.0-300M (NASA–IBM) fine-tune land cover (Sen4Map) บน Colab → export ONNX → วางใน `models/`
- ไฟล์หลัก: `main.py`, `agent/` (planner/registry/tools/memory/llm), `geo/` (io/tiling/indices/landcover/pipeline/visualize), `scripts/` (make_test_tiff/fetch_sample_data/finetune), `notebooks/02_finetune_landcover_colab.ipynb`, `static/`, `templates/`
- ติดตั้งเพิ่มใน env `ml`: rasterio, opencv-python-headless, onnxruntime, folium, onnxscript, onnx

### ทดสอบผ่าน (ก่อนปิดงาน)
- `scripts/make_test_tiff.py` ✅ สร้าง data/sample/test.tif (512×512, 6 แบนด์, EPSG:32648, 30ม./px)
- pipeline baseline ✅ จำแนก 4 คลาส + NDVI/NDWI/NDBI + พื้นที่ (เฮกตาร์/ตร.กม.)
- agent rule-based ✅ 'ช่วยด้วย / จำแนก land cover / สถิติพื้นที่ / คำนวณ NDWI / อธิบายคลาส' ครบทุก intent
- Flask (test client) ✅ GET /, /api/upload, /api/chat, /outputs/* (ภาพ PNG ออก HTTP 200)
- `scripts/finetune.py --synthetic` ✅ เทรน+eval+export ONNX (1,1,6,224,224)→(1,4,224,224) — fallback CNN เล็กเมื่อไม่มี terratorch/GPU
- แอป + ONNX รวมกัน ✅ pipeline สลับโหมด baseline → **Prithvi (ONNX)** อัตโนมัติเมื่อมี .onnx ใน models/ (tiling 224/112 + stitch + class_names.json + export GeoTIFF)
- **ข้อมูลจริง (HLS Mexico จาก repo Prithvi-EO-2.0-300M)** ✅ ดาวน์โหลด data/sample/mexico_hls.tif (6 แบนด์ int16, 560×448, EPSG:32613) — pipeline อ่าน/จำแนก/NDVI/พื้นที่ ผ่าน

### บันทึก
- คอนโซล Windows (cp1252) อ่านไทยไม่ได้ → ต้อง `PYTHONIOENCODING=utf-8` (แก้ในสคริปต์แล้วบางส่วน)
- **Prithvi-EO-2.0-300M ไม่ gated** (Apache-2.0) — ดาวน์โหลดได้เลยไม่ต้องยอมรับ license; login HF จำเป็นตอน push โมเดล
- preprocessing ของ IBM (inference.py): z-score ตาม config.json สำหรับ MAE pretrained — แต่โมเดลที่ fine-tune จาก Sen4Map ใช้ constant_scale 0.0001 (= /10000) ซึ่งตรงกับ geo/indices.to_reflectance แล้ว
- baseline มีขีดจำกัด: NDBI แยกเมืองกับดินโล่งไม่ออก (Mexico tile ได้ built-up เกินจริง) — รอโมเดล Prithvi จริงแก้
- `models/prithvi_landcover_demo.*` คือโมเดลทดสอบ (CNN เล็ก) **ย้ายไป models/demo/** แล้ว — ลบทิ้งได้เมื่อได้โมเดลจริง

## 2026-08-23 (รอบ 2) — เล่นกับโมเดลจริง + เจอข้อมูลสำคัญ
- ✅ login HF สำเร็จ (`Peeradon4778`) — token จาก `hf auth login`
- ✅ ดาวน์โหลด checkpoint จริง `Prithvi_EO_V2_300M.pt` (1.33GB) + config/prithvi_mae.py/inference.py ไว้ที่ `models/pretrained/`
- ✅ ดาวน์โหลดภาพตัวอย่างจริงครบ 4 เฟรม HLS Mexico (T13REM) ไว้ที่ `data/sample/`
- ✅ **รัน MAE reconstruction บน CPU ได้จริง: 1.1 นาที/ชุด 4 เฟรม** (โมเดล 330M params) → outputs/mae_demo/preview_t0..3.png (4 แผง: ต้นฉบับ/สร้างใหม่/mask/ซ้อนทับ)
- 🔍 **ค้นพบ: pretrain bands = B02,B03,B04,B05,B06,B07** (น้ำเงิน→เรดเอจ) — ไม่ใช่ NIR/SWIR; config.json มี mean/std สำหรับ z-score; โมเดลฝึกด้วย 4 time steps
  - ผลต่อโครงการ: `finetune.py` เลือกแบนด์ index 0–5 ของ Sen4Map = ตรงกับ pretrain bands พอดี ✅
  - ภาพที่อัปโหลดเข้าแอปต้องเลือกแบนด์ B02–B07 (แก้ docstring geo/landcover.py แล้ว)
- ✅ เขียน `notebooks/01_explore_prithvi.ipynb` — ดู MAE reconstruction บน CPU
- เพิ่ม `einops` ใน env `ml` (inference.py ของ IBM ต้องการ)
- ทดสอบ: notebook 01 JSON ผ่าน, inference.py รันจบ returncode 0

## 2026-08-23 (รอบ 3) — de-risk โค้ดเทรน + รวม repo GitHub
- ✅ ติดตั้ง `terratorch 1.2.11` ใน env `ml` (ไม่กระทบ torch/torchvision เดิม) และทดสอบ `PrithviModelFactory` จริงบน CPU
- 🔧 แก้ API terratorch 1.2.x 3 จุด: (1) `PrithviModelFactory()` ต้อง instantiate ก่อน (2) ใช้ `ckpt_path=` แทน `pretrained_cfg_overlay` (ถูกถอดออกแล้ว) (3) ชื่อ decoder ต้องเป็น `UperNetDecoder` (r ตัวเล็ก)
- ✅ `finetune.py --synthetic` + checkpoint จริง: โหลด Prithvi-EO-2.0-300M + UPerNet + เทรน + export ONNX (1,1,6,224,224)→(1,4,224,224) ผ่าน — แต่ smoke onnx ถูกลบแล้ว (เทรนแค่ 1 epoch บนข้อมูลจำลอง)
- ✅ เปลี่ยนชื่อ notebook: `01_explore_prithvi` → `03-explore-prithvi-mae`, `02_finetune_landcover_colab` → `04-finetune-landcover-colab` (ให้เลขต่อจาก learning path เดิม 01/02)
- 📦 **รวม repo GitHub**: merge งานนี้เข้ากับ `github.com/Tutorzaa/GISGPT` (branch main) — รวมประวัติทั้ง 2 ฝั่ง (ของเดิม: platform/OpenLayers + prototype + learning notebooks)
- 📝 อัปเดตเอกสาร: README ใหม่ (สถาปัตยกรรม agent + ผลทดสอบ + roadmap), satellite-data.md (API ล่าสุด: Copernicus STAC, NASA GIBS/POWER, NSDC), gistda-data.md (+NSDC/THEOS-2), PROTOTYPE.md (ชี้ระบบใหม่)
- ผล: merge คอนฟลิกแค่ .gitignore + requirements.txt (รวมกันแล้ว)

## 2026-08-23 (รอบ 4) — Phase A: ระบบ hotspot บุรีรัมย์ 🚜🔥

### สำรวจข้อมูล (พบว่าฟรี/สาธารณะ)
- **GISTDA ArcGIS REST services เปิดสาธารณะ** (ไม่ต้องคีย์!): `gistdaportal.gistda.or.th/data/rest/services`
  - `FR_Fire/hotspot_daily` (Aqua/Terra) — fields: confident(0-100), satellite, datetime, lu_name, ตำบล/อำเภอ/จังหวัด
  - `FR_Fire/hotspot_npp_daily` (NOAA-20 VIIRS) — confident(text), date/time, lu_name
  - `FR_Fire/AirQuality_daily` — 70 สถานี: st_name, pm25, pm10, lat/lon, จังหวัด
- ข้อมูล hotspot ทั้งหมดเป็นวันเดียว: **2023-04-06** (ฤดูเผา ก.พ.–เม.ย. พอดี) — 532 + 1001 จุดทั้งประเทศ
- ขอบเขต 77 จังหวัด: `apisit/thailand.json` (GeoJSON, ชื่ออังกฤษ) → บุรีรัมย์ polygon 523 จุด
- **สถานีฝุ่นใกล้บุรีรัมย์สุด: 47t โคราช (~90กม.)** — สถานีในอีสานน้อย (ประเด็นวิจัย Phase B)

### สร้าง
- `geo/hotspots.py` — ดึง GISTDA + FIRMS (ถ้ามีคีย์) → normalize → point-in-polygon → จัดอันดับ score (FRP/confidence) + cache 1 ชม.
- `scripts/fetch_hotspots.py` — CLI: `--province บุรีรัมย์` / `--bbox` / `--days`
- `templates/hotspots.html` — แผนที่ Leaflet: ขอบเขตจังหวัด + จุดสีตามความรุนแรง + popup + ตาราง Top 10 + legend
- `main.py` — routes `/hotspots` + `/api/hotspots?province=`
- agent: tool `fire_hotspots` + planner keywords (เผา/ไฟ/hotspot/จุดความร้อน)

### ทดสอบผ่าน
- fetch: 13 จุดในบุรีรัมย์ (Aqua 4, Terra 2, NOAA-20 VIIRS 7) — พื้นที่เกษตร 8, เขต สปก. 3, ป่าสงวน 1, ชุมชน 1 — อันดับ top: 97, 84, 73
- API `/api/hotspots` ✅ | หน้า `/hotspots` HTTP 200 ✅ | agent "จุดไหนในบุรีรัมย์มีการเผา" ✅ (curl ไทยพังเพราะ cp1252 — browser/py client ปกติ)

### หมายเหตุ
- ข้อมูล GISTDA เป็นชุดตัวอย่าง (วันเดียว) — ใช้เป็น demo/validation; FIRMS (ถ้ามีคีย์) จะให้ข้อมูลสด
- Phase B ต่อไป: ดึง AirQuality_daily + spatial join กับ hotspot 47t โคราช + correlation

## 2026-08-23 (รอบ 5) — Phase B: ได้ผล correlation จริง! 📊

### สร้าง backend Phase B
- `geo/analysis.py` — engine: Haversine, สถานีใกล้สุด, Pearson r/p (scipy), cross-sectional, time-series, scatter PNG
- `geo/airquality.py` — fetchers: GISTDA AQ (✅ 70 สถานี), FIRMS archive (✅), OpenAQ v3 (❌ ไม่มีสถานีไทยแล้ว), CAMS EAC4 (รอคีย์)
- `scripts/fetch_phaseb.py` — CLI: `--date` (cross-sectional) / `--timeseries` (รายวัน)
- API: `/api/airquality` ✅ + `/api/correlation`
- `.env` loader + `.env.example` (FIRMS/OpenAQ/CAMS) — โหลดอัตโนมัติทุก entry point

### 🔍 ข้อจำกัดข้อมูลที่เจอ (สำคัญ)
- GISTDA AQ (2020-08-29) กับ GISTDA hotspot (2023-04-06) **คนละวัน** — เทียบตรงๆ ไม่ได้
- Air4Thai/PCD API ตาย (403/404) · OpenAQ ไม่มีสถานีไทยใน v3 แล้ว
- FIRMS API format เปลี่ยน: ต้องใช้ `/{DAY_RANGE}/{YYYY-MM-DD}` + `_SP` (Standard Processing) สำหรับข้อมูลเก่า

### ✅ ผล Phase B จริง (FIRMS archive + GISTDA AQ วันที่ 2020-08-29, รัศมี 100 กม.)
- hotspot: 123 จุด (VIIRS 122 + MODIS 1) · สถานีที่มี hotspot+pm25: 52/70
- **correlation hotspot_count vs PM2.5: r=0.326, p=0.0059 (n=70) — มีนัยสำคัญ**
- **correlation hotspot_sum_frp vs PM2.5: r=0.319, p=0.0071 — มีนัยสำคัญ**
- สรุป: สถานีที่อยู่ใกล้ hotspot มาก → PM2.5 สูงขึ้นจริง (ภาพดาวเทียมยืนยันกับฝุ่น)
- scatter: outputs/phaseb_20200829_hotspot_count.png + _hotspot_sum_frp.png

### เตรียม CAMS (time-series เม.ย. 2023)
- ติดตั้ง cdsapi 0.7.7 + สร้าง C:\Users\User\.cdsapirc แล้ว — เหลือผู้ใช้สมัคร ADS แล้ววางคีย์ (UID:APIKEY)

## 2026-08-23 (รอบ 6) — CAMS ทำงาน + ผล time-series (ผลลบเชิงเวลา!) 🌫️

### แก้บั๊ก CAMS/ADS 2.0 (เจอจาก form.json ของ ADS)
- ชื่อตัวแปรจริง: `particulate_matter_2.5um` (ไม่ใช่ _2.5) — 400 error เงียบๆ
- ต้องกดยอมรับ **Terms of Use** ที่หน้า dataset (403 licence) — ผู้ใช้กดแล้ว ✅
- ไฟล์ netCDF: dim = `valid_time` (ไม่ใช่ time) · ตัวแปร = `pm2p5` · **หน่วย kg/m³ → ต้อง ×1e9 เป็น µg/m³** (แรกได้ 0.0 เพราะปัดค่าที่ ~1e-8)
- cdsapi ต้องโหลดเป็นไฟล์ (target) ไม่ใช่เปิด URL ตรงๆ
- ติดตั้งเพิ่ม: netCDF4 (xarray เปิด .nc ได้)

### ✅ ผล Phase B ครบ 2 มิติ (honest findings)
**เชิงพื้นที่ (cross-sectional, 2020-08-29, 70 สถานี, FIRMS archive):**
- hotspot 123 จุด · สถานีที่มี hotspot+pm25: 52/70
- **r = 0.326, p = 0.0059 (hotspot_count vs PM2.5) — มีนัยสำคัญ ✅**
- **r = 0.319, p = 0.0071 (sum_frp vs PM2.5) — มีนัยสำคัญ ✅**
- = สถานีที่อยู่ใกล้ hotspot เยอะ → PM2.5 สูงจริง

**เชิงเวลา (time-series, เม.ย. 2023 บุรีรัมย์, FIRMS FRP/วัน vs CAMS PM2.5/วัน):**
- hotspot 469 จุด (เฉพาะจังหวัด) / 3,733 จุด (รัศมี 1°) · PM2.5 30 วัน (19.6–68.8 µg/m³, เฉลี่ย 41.5)
- **lag 0/1/2/3 + FRP 3วันเฉลี่ย: r ≈ 0 ทุกรายการ (p > 0.5) — ไม่พบความสัมพันธ์รายวัน ❌**

### อธิบายผลลบ (สำหรับเขียนผลงาน)
1. CAMS EAC4 grid 0.75° (~80 กม.) กลบสัญญาณไฟในจังหวัดเดียว
2. เม.ย. 2023 ภาคอีสานไฟเยอะทั่วทั้งภูมิภาค (3,733 จุด) → PM2.5 อิ่มตัวสูงทุกวัน (สัญญาณรายวันหาย)
3. ลม/ฝน/แหล่งฝุ่นอื่น (เมือง โรงงาน) มีผลต่อ PM2.5 รายวันมากกว่าไฟในจังหวัดเดียว

**บทสรุป Phase B:** ภาพดาวเทียมยืนยันกับฝุ่น**เชิงพื้นที่**ชัดเจน แต่**เชิงเวลา**ที่ scale จังหวัดต้องใช้ข้อมูลความละเอียดสูง (สถานี PCD รายชั่วโมง หรือ AOD 1 กม.) — เป็นข้อเสนอ/ข้อจำกัดที่เขียนลงผลงานได้

### ไฟล์ผลลัพธ์
- outputs/phaseb_20200829_hotspot_count.png + _hotspot_sum_frp.png (cross-sectional)
- outputs/phaseb_บุรีรัมย์_timeseries.png (time-series)
- data/processed/phaseb_*.json (ข้อมูลดิบที่วิเคราะห์)

## 2026-08-24 (รอบ 7) — Prototype Dashboard สไตล์ Fire Emissions Watch 🖥️

### สร้าง (ตามโจทย์: แผนที่ + แผงกราฟซ้าย + AI agent)
- `geo/dashboard.py` — รวมข้อมูล FIRMS archive หลายวัน → สรุป + อนุกรมรายวัน + แยกจังหวัด (shapely point-in-polygon, โหลด 77 จังหวัดครั้งเดียว)
- `templates/dashboard.html` + `static/css/dashboard.css` + `static/js/dashboard.js` — ธีมเขียวเข้ม #0F4A57 ตาม reference, Leaflet (แผนที่จุดไฟสีตาม FRP) + ECharts (กราฟ FRP/วัน, แยกจังหวัด) + แชท AI agent
- routes: `/dashboard` + `/api/dashboard?province=&start=&end=`

### ทดสอบผ่าน
- backend 7 วัน (2023-04-01..07): 357 จุด FRP 2150.2, peak 2023-04-05 (874 FRP), แยกจังหวัดถูก (บุรีรัมย์ 75, โคราช 70, ร้อยเอ็ด 54...) — 8.3 วิ/7 วัน
- `/dashboard` HTTP 200 · `/api/dashboard` 200 ✅

### บันทึก/ข้อจำกัด
- จุดใน bbox ติดชายแดนกัมพูชา = "(นอกไทย/ทะเล)" (ยังไม่กรอง polygon ชายแดน)
- FIRMS SP ดีเลย์ ~7-10 วัน → ข้อมูลสดต้องใช้ NRT (TODO)
- reference ใช้ MapLibre+deck.gl+ECharts; prototype ใช้ Leaflet+ECharts (เบากว่า)
- เขียน `docs/DASHBOARD.md` — วิธีทำ/กระบวนการ/สถาปัตยกรรม/roadmap

## 2026-08-24 (รอบ 8) — Phase C: การเปลี่ยนแปลงพื้นที่สีเขียว/เมือง 📗🟤

### สร้าง (ต่อตาม BURN_MONITORING_PLAN Phase C)
- `geo/greenchange.py` — engine เปรียบเทียบ 2 ช่วงเวลา (ฉากเดียวกัน): คำนวณ ΔNDVI (เขียว) + ΔNDBI (เมือง) รายพิกเซล → 5 คลาส
  (0 ไม่เปลี่ยน / 1 เขียวเพิ่ม / 2 เขียวลด / 3 เมืองขยาย / 4 เมืองลด) + สถิติพื้นที่ (ha/km²) + ผลสุทธิ
  - 🔑 แก้การชนกัน: เกณฑ์เมืองต้อง**ลิ่มด้วยค่า NDBI สัมบูรณ์** (NDBI₂ สูง=เป็นตึกจริง) เพื่อแยก "โล่ง→กลับเขียว" (ΔNDBI ลดด้วยเช่นกัน) ออกจาก "เมืองลด"
- `scripts/make_change_test_tiff.py` — สร้างภาพจำลอง t1/t2 256×256 (4 โซนเปลี่ยนชัดเจน + น้ำ/เมือง/โล่ง)
- `scripts/fetch_stac_sentinel2.py` — ค้นหา/จัดอันดับ Sentinel-2 L2A ผ่าน Copernicus STAC (metadata ฟรี ไม่ต้อง login)
  + โหลด 6 แบนด์ [B02,B03,B04,B08,B11,B12] = Blue..SWIR2 (ตรง geo.indices) พร้อม resample 20ม.(B11/B12)→10ม. — ต้องมี COPERNICUS_USER/PASSWORD ใน .env
- agent tool `green_change` + planner keyword (เปรียบเทียบ/เปลี่ยนแปลง/เมืองขยาย/สองช่วง/...) — รู้เมื่อมีภาพ 2 ภาพใน session
- `main.py`: route `POST /api/greenchange` (ส่ง t1/t2 ไฟล์) + เก็บ `session["images"]` ย้อนหลัง 12 ภาพ

### ทดสอบผ่าน
- engine จำลอง: ทั้ง 5 คลาส**ตรงเป๊ะ**ตามโซนที่ตั้ง (c0 57136 / c1 2400 / c2 2000 / c3 2500 / c4 1500 px) + net_green/net_built ถูก ✅
- `fetch_stac_sentinel2.py --search-only` (บุรีรัมย์ bbox, มี.ค./เม.ย.2023) ← หา scene ไร้เมฆจริง (0% / 7.45% cloud) ✅
- Flask test client: อัปโหลด 2 ภาพ → แชท "เปรียบเทียบ..." → สถิติ 5 คลาส + แผนที่ diff (artifact) ✅ · `/api/greenchange` POST → HTTP 200 + stats ✅

### หมายเหตุ/ข้อจำกัด
- ต้องใช้ภาพตรวจภูมิ (co-registered) ขนาดเท่ากัน — สคริปต์ STAC จะ handling resample ให้แล้ว
- แบนด์สำหรับ NDVI/NDBI = [B02,B03,B04,B08,B11,B12] (มี NIR/SWIR) — **ต่างจาก** Prithvi (B02–B07 RedEdge)
- โหลดแบนด์จริงยังไม่ทดสอบ (ต้องมีบัญชี Copernicus) — ค้นหา/จัดอันดับทำงานแล้ว
- (TODO) เชื่อมกับ Phase A: นับ hotspot ในโซนที่เขียวลด

## 2026-08-24 (วางแผนใหญ่ — pivot วิสัยทัศน์แพลตฟอร์ม แยก 27 tasks)
### ทิศทางใหม่ (จากผู้ใช้)
- แพลตฟอร์ม **Windy-like** ผสาน **ข้อมูลดาวเทียม + สภาพอากาศ (met)** บนแผนที่ สั่งผ่าน **แชทบอท AI** (Geospatial Foundation Model) → แสดงผลเป็น data point บนแผนที่ + **กราฟ correlation** เพื่อพิสูจน์ผล
- มุมวิจัย: ใช้ GFM วิเคราะห์/ยืนยันเหตุการณ์เชิงพื้นที่-เวลา, verify ความเข้าใจโมเดล, benchmark spatio-temporal
- ผู้ใช้ตัดสินใจ: **ยังไม่ทำ UI** — เริ่มจากโครง backend + เอกสารสถาปัตยกรรม/แผนก่อน

### เอกสารที่เขียน
- `docs/PLATFORM_ARCHITECTURE.md` — สถาปัตยกรรม 4 ชั้น (frontend/agent/analysis/adapters) + normalized row `{lat,lon,time,metric,value,src}` + tech stack + API + แผน P0–P4 + เปิดคำถาม
- `.scratch/gisgpt-platform/README.md` — แผนผัง dependencies + critical path
- `.scratch/gisgpt-platform/issues/01–27-*.md` — **27 tasks ย่อย ๆ** แต่ละไฟล์มี What to build / Blocked by / acceptance

### แนวทิศทางที่ลงตัว
- critical path: 01→02→(04/05/06→08→09) และ 03→(14/15/16)→18→23→27
- ชิ้นแรกที่เป็น "usable" เร็วสุด: **09 `/api/correlation`** (hotspot↔met) พิสูจน์ห่วงโซ่ด้วย API ตรง
- ผู้ใช้คนแรก: **18 `/api/query`** (ภาษาไทย → data point + layer + chart)
- ยังไม่ได้แก้โค้ด function ในรอบนี้ (เป็นงานวางแผน/documentation เท่านั้น)

## 2026-08-24 (ไล่ทำงานตาม Ticket — start)
### Ticket 01 ✅ — โครง backend + schema + cache (รากฐาน)
- `config.py` — โหลด .env + ค่าคงที่ (DATA_RAW/OUTPUTS/CACHE_DIR) ใช้ร่วมกัน
- `core/normalize.py` — **NormalizedRow** `{lat,lon,time,metric,value,src,meta}` + validate + make/from_dict/to_records + `to_geojson()`
- `core/cache.py` — `JSONCache` (TTL, key SHA1 ปลอดภัย, get/set/delete/clear)
- `tests/test_core.py` — **19 tests ผ่าน** ✅ (validate, roundtrip, geojson, cache ttl/delete/clear)

### Ticket 03 ✅ — agent tool contract (map layer + chart)

- `agent/__init__.py` `_compose` — รวม `data_points/layers/chart` เข้า reply + `agent/tools.py` docstring สัญญาใหม่ + `tests/test_agent_contract.py` (30 tests ผ่าน ✅)

### Ticket 02 ✅ — geometry utils

- `core/geometry.py` — haversine/bbox_center/grid/point-in-polygon/buffer + `tests/test_geometry.py` (26 tests ผ่าน ✅)

### หมายเหตุ
- เริ่มทำตามแผนทิศทาง: 01 (base) → 02 (geometry) → 03 (agent contract) → 04–06 (adapter)
- เหลือติดตั้ง pytest ใน env dev (ติดแล้วใน .venv)
