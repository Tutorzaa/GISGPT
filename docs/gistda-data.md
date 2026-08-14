# ข้อมูล GISTDA Open Data — คู่มือใช้งาน

ที่มา: https://opendata.gistda.or.th (ระบบ CKAN — เข้าถึงผ่าน API สด ไม่ได้เก็บข้อมูลบน GitHub)

## 1. วิธีเข้าถึง

| API | ต้องใช้คีย์? | ใช้ทำอะไร |
|---|---|---|
| CKAN API `https://opendata.gistda.or.th/api/3/action/` | ไม่ต้อง | ค้นหาชุดข้อมูล (`package_search`), ดูรายละเอียด (`package_show`) |
| API Gateway `https://api-gateway.gistda.or.th/api/2.0/` | **ต้องสมัคร** | ดึงข้อมูลจริง เช่น พื้นที่ปลูกข้าว, น้ำท่วม, ภาพดาวเทียม 2 เมตร |

## 2. สมัคร API key (ฟรี)

1. ไปที่ https://api-gateway.gistda.or.th
2. ลงทะเบียนด้วยอีเมล
3. สร้าง/ดู API key ของตัวเอง
4. หมายเหตุ: คีย์ที่แปะอยู่ใน URL ของ resource บน portal เป็นคีย์ตัวอย่าง/หมดอายุแล้ว — ต้องใช้คีย์ของตัวเอง

## 3. ชุดข้อมูลที่น่าสนใจสำหรับ GISGPT

| ชุดข้อมูล | dataset ID | endpoint (ย่อ) |
|---|---|---|
| ภาพถ่ายดาวเทียม 2 เมตร ล่าสุด | `2-gistda`, `basemap-2568` | `tiles/gi-basemap_68/{z}/{x}/{y}.png` (XYZ tile ใช้กับ Leaflet ได้) |
| พื้นที่ปลูกข้าว | `dataset_2024_03` | `gi-service/v2.2/agriculture/rice-weekly-40m` |
| พื้นที่ปลูกข้าวโพด | `dataset_2024_04` | `.../corn-weekly-40m` |
| พื้นที่ปลูกมันสำปะหลัง | `dataset_2024_02` | `.../cassava-weekly-40m` |
| พื้นที่ปลูกอ้อย | `dataset_2024_01` | `.../sugarcane-weekly-40m` |
| พื้นที่ปลูกปาล์มน้ำมัน | `dataset_2024_05` | `.../oilpalm-weekly-40m` |
| พื้นที่ปลูกยางพารา | `dataset_2024_06` | `.../rubber-weekly-40m` |
| พื้นที่น้ำท่วมซ้ำซาก (2011–2023) | `disasters-01` | `gi-service/v1.1/disasters/flood-recurrence` |
| พื้นที่ภัยแล้งซ้ำซาก (2018–2023) | `disasters-02` | `gi-service/v1.1/disasters/drought-recurrence` |
| พื้นที่เผาไหม้ (ล่าสุด) | `disasters-04` | `gi-service/v1.1/disasters/burnt-area` |
| PM2.5 | `pm2-5` | JSON |
| ความชื้นในดินของประเทศไทย | `fundamental-01` | API |

> endpoint ที่แน่นอนของแต่ละชุดข้อมูลให้ดูผ่าน `notebooks/02-gistda-open-data.ipynb` (ฟังก์ชัน `show_dataset`)

## 4. วิธีใช้ในโปรเจกต์ GISGPT

### แผนที่ (basemap 2 เมตร)
ใส่ API key ใน `prototype/js/app.js` ตัวแปร `GISTDA_KEY` แล้วปุ่มสลับเลเยอร์จะเพิ่มตัวเลือก **GISTDA 2M**

```js
const GISTDA_KEY='xxxxxxxxxxxxxxxx'; // คีย์ที่สมัครจาก api-gateway.gistda.or.th
```

### วิเคราะห์ข้อมูล (backend / notebook)
- แบบจุด: `?lat=13.75&lon=100.5&api_key=KEY`
- แบบพื้นที่: `?area={"type":"Feature","properties":{},"geometry":{"coordinates":[[[lon,lat],...]],"type":"Polygon"}}&api_key=KEY`

ดูตัวอย่างโค้ดใน `notebooks/02-gistda-open-data.ipynb`

## 5. ข้อควรระวัง

- ชุดข้อมูลแต่ละชุดมี endpoint ต่างกัน — ตรวจสอบ URL จาก `package_show` ทุกครั้ง
- บาง service จำกัดสิทธิ์ตามเงื่อนไขของชุดข้อมูล
- อ่านรายละเอียดลิขสิทธิ์ (ส่วนใหญ่เป็น Open Data Common) ที่หน้าแต่ละชุดข้อมูล
