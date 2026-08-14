# แหล่งข้อมูลภาพถ่ายดาวเทียม (ฟรี)

คำแนะนำแหล่งดาวน์โหลดภาพถ่ายดาวเทียมสำหรับฝึกวิเคราะห์และใช้ใน GISGPT

## 1. Sentinel-2 (แนะนำ) — ESA

- **ความละเอียด:** 10 เมตร (bands B2, B3, B4, B8)
- **ความถี่:** ทุก ~5 วัน ครอบคลุมทั้งโลก รวมถึงประเทศไทย
- **ราคา:** ฟรี 100%
- **วิธีดาวน์โหลด:**
  1. สมัครบัญชีฟรีที่ [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
  2. เข้า [Copernicus Browser](https://browser.dataspace.copernicus.eu/)
  3. เลือกเครื่องมือค้นหา → กรอง `Sentinel-2` → ระบุช่วงวันที่ และเลือกพื้นที่
  4. เลือกภาพที่มีเมฆน้อย (ดูคอลัมน์ Cloud cover)
  5. กดดาวน์โหลดแบบ **L2A (Surface Reflectance)** → เลือกไฟล์ *10m* และเลือก band ที่ต้องการ (B02–B08, B11, B12)
  6. ได้ไฟล์ GeoTIFF นำไปใช้กับ notebook ได้เลย

**หมายเหตุ:** ควรใช้ภาพ L2A (ผ่านการแก้บรรยากาศแล้ว) ไม่ใช่ L1C

## 2. Landsat 8/9 — NASA/USGS

- **ความละเอียด:** 30 เมตร
- **ความถี่:** ทุก 16 วัน
- **ข้อดี:** ข้อมูลย้อนหลังยาวนานตั้งแต่ปี 1984 เหมาะกับการศึกษาการเปลี่ยนแปลง
- **วิธีดาวน์โหลด:** [USGS EarthExplorer](https://earthexplorer.usgs.gov/) (ต้องสมัครบัญชีฟรี)
- ใช้ Collection 2 Level-2 (Surface Reflectance)

## 3. Google Earth Engine (GEE) — ไม่ต้องดาวน์โหลด

- ทำงานบน cloud ดึงภาพทั้งแคตตาล็อก Sentinel-2/Landsat มาคำนวณได้เลย
- เหมาะกับเมื่อต้องการประมวลผลหลายพื้นที่หรือหลายช่วงเวลา
- เริ่มที่ [code.earthengine.google.com](https://code.earthengine.google.com/) (สมัครฟรี)
- ใช้ได้ทั้ง JavaScript (ในเว็บ) และ Python (`earthengine-api`)

## สรุปเส้นทางแนะนำ

| ขั้น | เครื่องมือ | ใช้ทำอะไร |
|---|---|---|
| 1. เรียนรู้ | Sentinel-2 + Jupyter notebook | ฝึกอ่านภาพ คำนวณ NDVI/NDWI |
| 2. วิเคราะห์ | GEE หรือดาวน์โหลด ROI | ดึงภาพตามพื้นที่ที่ผู้ใช้เลือก |
| 3. เชื่อมเว็บ | Python backend (FastAPI/Flask) | รับพิกัด ROI → วิเคราะห์ → ส่งผลกลับ |
