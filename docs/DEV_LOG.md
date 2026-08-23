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
