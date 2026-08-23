# 🚜 แผนระบบเฝ้าระวังการเผาไร่เผานา + ยืนยันด้วยฝุ่น/อุณหภูมิ (GISGPT)

> **เป้าหมาย:** ผู้ใช้ถามเป็นภาษาไทย เช่น *"ขอพื้นที่พร้อมพิกัดในจังหวัดบุรีรัมย์ว่าบริเวณใดบ้างมีการเผาไร่เผานา"*
> ระบบตอบกลับด้วย **แผนที่ขอบเขตจังหวัดบุรีรัมย์ + ระบายสีจุด hotspot + จัดอันดับพิกัดความรุนแรง**
> และ **ยืนยันข้ามข้อมูล** ว่าค่าฝุ่น PM2.5 / อุณหภูมิ ตรงกับภาพถ่ายดาวเทียมหรือไม่
> ขยายไปสู่การตรวจจับ **การเปลี่ยนแปลงพื้นที่สีเขียว / การขยายตัวของเมือง** ตามช่วงเวลา

---

## 1. ข้อมูลที่ต้องใช้ (ฟรีทั้งหมด)

| # | ข้อมูล | แหล่ง | ต้องสมัคร? | ใช้ทำอะไร |
|---|---|---|---|---|
| ① | **จุดความร้อน hotspot** | **GISTDA** FR_Fire (`hotspot_daily` / AirQuality service) — ข้อมูลในไทย | ✅ api-gateway.gistda.or.th (คีย์ฟรี) | จุดเผาในบุรีรัมย์ + พิกัด + FRP |
| ①b | **จุดไฟ active fire** | **NASA FIRMS** (VIIRS 375ม. / MODIS) `firms.modaps.eosdis.nasa.gov` | ✅ Earthdata + MAP_KEY (ฟรีทางอีเมล) | hotspot ระดับโลก 375ม. + FRP — ใช้ cross-check/backup |
| ② | **ขอบเขตจังหวัด** | `chingchai/OpenGISData-Thailand` (GeoJSON 77 จังหวัด, ชื่อไทย+อังกฤษ) หรือ GADM 4.1 | ❌ | วาดขอบเขตบุรีรัมย์ + กรองจุดที่อยู่ในจังหวัด |
| ③ | **ฝุ่น PM2.5 / อุณหภูมิ** | **GISTDA** `AirQuality_daily`/`AirQuality_hourly` + `sds.gistda.or.th` (600+ สถานี) | ✅ คีย์เดียวกับ ① | ยืนยันว่า hotspot ตรงกับฝุ่น/อุณหภูมิจริงไหม |
| ④ | **ภาพ Sentinel-2** | Copernicus Data Space **STAC API** (`catalogue.dataspace.copernicus.eu/stac`) | ✅ (ฟรี) | Phase C: เปรียบเทียบพื้นที่สีเขียว/เมือง 2 ช่วงเวลา |
| ⑤ | ฐาน pipeline | GISGPT: `geo/` + `agent/` + OpenLayers `platform/` | — | มีแล้ว ต่อยอด |

**ฤดูกาลอ้างอิง:** ฤดูเผาไร่ในภาคอีสาน ≈ **ก.พ.–เม.ย.** (หลังเก็บเกี่ยวข้าวนาปรัง/เตรียมแปลง) — ใช้ช่วงนี้เทียบ validation

---

## 2. สถาปัตยกรรม

```
ถาม: "จุดไหนในบุรีรัมย์มีการเผา + ฝุ่นตรงไหม?"
  │
  ▼
┌─ agent (ต่อยอด agent เดิม) ──────────────┐
│ tools ใหม่:                              │
│  • fire_hotspots(province, date)         │
│  • province_boundary(province)           │
│  • pm25_weather(lat, lon, date)          │
│  • green_change(bbox, t1, t2)            │
│  planner: rule-based + LLM (HF)          │
└───────────────┬──────────────────────────┘
                ▼
┌─ data layer ─────────────────────────────┐
│ GISTDA hotspot/AQI  ·  FIRMS  ·  GeoJSON │
│ ขอบเขตจังหวัด  ·  Copernicus STAC (S2)    │
└───────────────┬──────────────────────────┘
                ▼
┌─ analysis ───────────────────────────────┐
│ 1. กรอง hotspot ด้วย polygon จังหวัด      │
│ 2. จัดอันดับตาม FRP (แรง→อ่อน)            │
│ 3. spatial join: hotspot ↔ สถานีฝุ่นใกล้  │
│ 4. correlation: FRP รวมรายวัน ↔ PM2.5    │
│ 5. (Phase C) NDVI/land cover diff 2 ยุค  │
└───────────────┬──────────────────────────┘
                ▼
┌─ output ─────────────────────────────────┐
│ แผนที่ขอบเขตจังหวัด + จุดสีตามความรุนแรง   │
│ ตารางอันดับพิกัด (lat, lon, FRP, วันที่)  │
│ scatter/correlation ฝุ่น-ไฟ  ·  export CSV│
└──────────────────────────────────────────┘
```

---

## 3. Phase A — MVP: แผนที่ hotspot บุรีรัมย์ + จัดอันดับ (เล็ก, ทำก่อน)

**Deliverable:** web page (ต่อยอด `main.py` หรือ `platform/`) แสดง:
- ขอบเขตจังหวัดบุรีรัมย์ (GeoJSON ②)
- จุด hotspot จาก GISTDA + FIRMS (①) — สีตามความรุนแรง FRP (เขียว=อ่อน → แดง=รุนแรง)
- ตารางจัดอันดับพิกัด 10 อันดับแรก (lat/lon, FRP, วันที่, แหล่งข้อมูล)
- export CSV

**ขั้นตอน:**
1. สมัครคีย์: GISTDA API Gateway + NASA Earthdata→FIRMS MAP_KEY
2. สำรวจ endpoint จริงของ GISTDA `FR_Fire/hotspot_daily` (docs ของ GISTDA ไม่สมบูรณ์ — ต้องลองจริง)
3. `scripts/fetch_hotspots.py` — ดึง hotspot (GISTDA + FIRMS) → normalize เป็น schema เดียว `{lat, lon, frp, date, source}`
4. `scripts/fetch_thailand_boundary.py` — ดาวน์โหลด GeoJSON 77 จังหวัด → กรองบุรีรัมย์
5. `geo/hotspots.py` — point-in-polygon กรองจุดในจังหวัด + จัดอันดับ FRP
6. Flask route `/api/hotspots?province=บุรีรัมย์&days=30` + แผนที่หน้าเว็บ (Leaflet/OpenLayers + จุดสี)

**การทดสอบ Phase A:**
- ดึงข้อมูลช่วง ก.พ.–เม.ย. (ฤดูเผา) จำนวนจุดต้อง > 0 และอยู่ใน polygon จังหวัด 100%
- จุด GISTDA กับ FIRMS ทับกัน/ใกล้กัน (ทั้งคู่มาจาก VIIRS/MODIS เดียวกัน)
- ตรวจ FRP สูงสุดตรงกับเขตเกษตร (นา/ไร่) ไม่ใช่ป่าอนุรักษ์

---

## 4. Phase B — ยืนยันด้วยฝุ่น/อุณหภูมิ (cross-validation)

**Deliverable:** รายงานความสัมพันธ์ hotspot ↔ คุณภาพอากาศ

**ขั้นตอน:**
1. `scripts/fetch_air_quality.py` — ดึง PM2.5 + อุณหภูมิรายวัน (GISTDA AirQuality_daily + sds.gistda.or.th)
2. หาพิกัดสถานีวัดฝุ่น — เลือกสถานีที่ใกล้บุรีรัมย์ที่สุด (อาจต้องใช้สถานีจังหวัดข้างเคียง: สุรินทร์/นครราชสีมา/ศรีสะเกษ เพราะสถานีในบุรีรัมย์อาจน้อย)
3. **spatial join:** แต่ละ hotspot → สถานีฝุ่นใกล้สุด (Haversine) + จับคู่ช่วงวัน
4. **Correlation:** FRP รวม/วัน ↔ PM2.5 เฉลี่ย/วัน (Pearson r + p-value) — ทดสอบทั้งแบบวันเดียวกันและ lag 0–3 วัน (ฝุ่นลอยตามลม)
5. อุณหภูมิ: เปรียบเทียบอุณหภูมิวันที่มี hotspot มาก vs น้อย
6. Output: scatter plot + ค่า r/p + ตาราง + บทสรุป "ภาพดาวเทียมยืนยันกับฝุ่นจริงหรือไม่"

**ข้อควรระวัง (ต้องพูดถึงในผลงาน):**
- ฝุ่นมาจากหลายแหล่ง (รถยนต์/โรงงาน/ข้ามพรมแดน) — correlation ไม่ใช่ causation
- ข้อมูลฝุ่นรายวันรายสถานีอาจขาดช่วง — จัดการ missing
- ทิศทางลมมีผล — ถ้ามีข้อมูลลม (sds.gistda.or.th) นำมาพิจารณาเพิ่มได้

---

## 5. Phase C — การเปลี่ยนแปลงพื้นที่สีเขียว / การขยายตัวของเมือง

**Deliverable:** แผนที่การเปลี่ยนแปลง 2 ช่วงเวลา + สถิติพื้นที่

**ขั้นตอน:**
1. Copernicus STAC: ค้นหา Sentinel-2 L2A ครอบ bbox บุรีรัมย์ 2 ช่วงเวลา (เช่น มี.ค.ปีนี้ vs มี.ค.ปีก่อน หรือต้น/ปลายฤดู)
2. เลือกภาพเมฆน้อย → ดาวน์โหลดแบนด์ B02–B07 (ตรงสัญญา Prithvi)
3. คำนวณ NDVI / land cover ทั้ง 2 ยุค (ใช้ pipeline เดิม + Prithvi ถ้าเทรนแล้ว)
4. **diff map:** พื้นที่สีเขียวลดลง (NDVI ลด) / เมืองขยาย (NDBI เพิ่ม) → ระบายสี 3 กลุ่ม (เขียวขึ้น/แย่ลง/คงเดิม)
5. สถิติ: พื้นที่เปลี่ยน net (ไร่/เฮกตาร์) + hotspot ในบริเวณที่สีเขียวลดลง (เชื่อมกับ Phase A)

**ข้อควรระวัง:** เปรียบเทียบภาพช่วงเวลาเดียวกันของปี (phenology ต่างฤดูจะตีความยาก) + เมฆ

---

## 6. Phase D — เลือกพื้นที่จากลูกโลก/แผนที่ + ผูกกับ agent + deploy

**Deliverable:** ระบบครบวงจร ใช้ได้จริง

**ขั้นตอน:**
1. **ROI บนแผนที่:** เพิ่มเครื่องมือเลือกพื้นที่ (rectangle/polygon) ใน `platform/` (OpenLayers — รองรับ globe view ในเวอร์ชันใหม่; ถ้าอยากได้ลูกโลกเต็มรูปแบบใช้ CesiumJS) → ส่ง bbox ไป backend
2. **agent tools:** `fire_hotspots(bbox, date_range)`, `province_boundary(province)`, `pm25_check(lat, lon, date)`, `green_change(bbox, t1, t2)` + ผูกเข้ากับ planner (rule-based + LLM ผ่าน HF token)
3. **ผลลัพธ์ในแชท:** แผนที่ hotspot + ตารางอันดับ + กราฟ correlation (เหมือน Phase A/B แต่สั่งด้วยภาษาธรรมชาติ)
4. **Deploy:** Hugging Face Spaces (Gradio/Flask) + หน้า landing Vercel
5. (optional) scheduler ดึง hotspot รายวันให้อัตโนมัติ

---

## 7. Timeline (ประมาณ)

| Phase | เวลาที่คาด | ต้องมีอะไรก่อน |
|---|---|---|
| A | 1–2 เซสชัน | คีย์ GISTDA + FIRMS |
| B | 2–3 เซสชัน | ผ่าน A |
| C | 2–3 เซสชัน | คีย์ Copernicus + (Prithvi เทรนแล้วจะดีมาก) |
| D | 2–3 เซสชัน | ผ่าน A–C |

---

## 8. Action items — ผู้ใช้ต้องสมัคร (ฟรี, ทำได้ทันที)

1. **GISTDA API key:** https://api-gateway.gistda.or.th → ลงทะเบียน → สร้าง key
2. **NASA FIRMS MAP_KEY:** https://firms.modaps.eosdis.nasa.gov/api/map_key/ (ต้องมี Earthdata login ก่อน: https://urs.earthdata.nasa.gov) — คีย์ส่งทางอีเมลทันที
3. (Phase C) **Copernicus Data Space:** https://dataspace.copernicus.eu

---

## 9. คำถามที่ยังต้องสำรวจตอนมีคีย์

- [ ] endpoint/รูปแบบจริงของ GISTDA `FR_Fire/hotspot_daily` และ `AirQuality_daily` (พารามิเตอร์, รูปแบบ, ต้องใช้ token แบบไหน)
- [ ] มีพิกัดสถานีวัดฝุ่นใน GISTDA ให้ไหม / สถานีไหนใกล้บุรีรัมย์สุด
- [ ] GISTDA hotspot มีคอลัมน์ FRP ไหม หรือมีแค่ตำแหน่ง+วัน
- [ ] ช่วงข้อมูลย้อนหลัง (กี่วัน/กี่ปี) ของ hotspot_daily

> หมายเหตุ: ระบบนี้เป็นโครงงานที่ทำได้จริงและมีคุณค่าทางวิชาการ (JSTP/YSC ได้) — **hotspot + ฝุ่น + การตรวจข้ามข้อมูล** เป็นธีมวิจัยสิ่งแวดล้อมที่กรรมการให้ความสนใจ
