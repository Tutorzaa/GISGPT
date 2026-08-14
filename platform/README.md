# GISGPT GIS Platform

แพลตฟอร์ม GIS บนเว็บ (OpenLayers) — เป็นฐานสำหรับพัฒนาไปสู่เครื่องมือวิเคราะห์แบบ QGIS และเชื่อม AI Agent ในอนาคต

## เปิดใช้งาน

เปิด `platform/index.html` ด้วยเบราว์เซอร์ตรง ๆ หรือรัน server ท้องถิ่น:

```bash
python -m http.server 8000 --directory platform
# แล้วเปิด http://localhost:8000
```

## ฟีเจอร์ (Phase 1 — MVP)

- แผนที่ OpenLayers + สลับ basemap (OSM / Esri Satellite / GISTDA 2ม.)
- **Layer Panel:** เปิด-ปิดชั้นข้อมูล, ปรับความโปร่งใส, เรียงลำดับ, ซูมเข้าชั้น, ลบชั้น
- **นำเข้าข้อมูล:** GeoJSON (.geojson/.json), Shapefile (.zip), KML, GPX — และปุ่ม LOAD SAMPLE ข้อมูลตัวอย่างกรุงเทพฯ
- **ตาราง attribute:** เปิดจากปุ่ม T, ค้นหา/กรอง, คลิกแถว → ไฮไลต์และเลื่อนแผนที่ไปยัง feature
- **Identify:** คลิกที่ feature บนแผนที่ → ดู attribute ใน popup
- **แถบสถานะ:** พิกัด LON/LAT (EPSG:4326), zoom, จำนวน features

## โครงสร้างโค้ด

```
platform/
├── index.html          — โครงหน้าเว็บ
├── css/style.css       — สไตล์ (ธีมเดียวกับ prototype)
└── js/
    ├── config.js       — basemap, สี, ข้อมูลตัวอย่าง, GISTDA key
    ├── map.js          — สร้างแผนที่, สลับ basemap, popup
    ├── layers.js       — จัดการชั้นข้อมูล + panel UI
    ├── import.js       — นำเข้า GeoJSON/Shapefile/KML/GPX
    ├── table.js        — ตาราง attribute + ค้นหา
    └── main.js         — เชื่อมต่อ UI ทั้งหมด
```

## ไลบรารี (CDN)

| ไลบรารี | ใช้ทำอะไร |
|---|---|
| OpenLayers 10.3 | แกนระบบแผนที่ |
| shpjs | อ่านไฟล์ Shapefile |
| @turf/turf | วิเคราะห์เชิงพื้นที่ (Phase 2: buffer/clip/intersect) |
| @mapbox/togeojson | แปลง KML/GPX → GeoJSON |

## Roadmap

- **Phase 2:** เครื่องมือวิเคราะห์ Turf.js (buffer, clip, intersect, dissolve) + เครื่องมือวัด
- **Phase 3:** Spatial SQL (DuckDB-WASM) + raster (GeoTIFF)
- **Phase 4:** บันทึก/โหลดโปรเจกต์, ส่งออก KML/GPKG
- **Phase 5:** AI Agent ต่อจากแพลตฟอร์มนี้

## หมายเหตุ

- GISTDA 2M basemap ต้องสมัคร API key ฟรีที่ https://api-gateway.gistda.or.th แล้วใส่ใน `js/config.js` (`GISGPT.GISTDA_KEY`)
- ข้อมูลตัวอย่างอยู่ใน `js/config.js` (`GISGPT.SAMPLE`) — ใช้ทดสอบได้ทันทีโดยไม่ต้องมีไฟล์
