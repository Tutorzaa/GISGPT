# GISGPT Backend — โครงสร้างโมดูล + API spec

> สถานะ: **ออกแบบต่อจาก `PLATFORM_ARCHITECTURE.md`** — ยังเป็นแผน ยังไม่ลงโค้ดใหม่ (งานนี้ = tasks 01–13 ใน `.scratch/gisgpt-platform/`)
> หลัก: ทุกแหล่งข้อมูล adjust เป็นแถวมาตรฐานเดียว → analysis/agent/API ทำงานบนชุดเดียวกันได้หมด

## 1. โครงสร้างแพ็กเกจหลัง rebuild (เป้าหมาย)

```
gisgpt/
├── main.py                 # Flask app + route ทั้งหมด
├── config.py               # โหลด .env + ค่าคงที่ (BASE_DIR, OUTPUTS, ฯลฯ)
├── datasources/            # ← ชั้น data adapters (Layer 1)
│   ├── satellite/
│   │   ├── gistda.py       # hotspot, AQ image  (reuse geo/hotspots)
│   │   ├── firms.py        # NASA FIRMS archive/NRT (key opts)
│   │   └── stac.py         # Copernicus STAC S2/Landsat (scripts/fetch_stac_sentinel2 → module)
│   ├── met/
│   │   ├── nasa_power.py   # ฟรี อุณหภูมิ/ฝน/ความชื้น
│   │   ├── cams_eac4.py    # PM2.5/เคมี (ต้องคีย์ ADS) — reuse geo/airquality
│   │   └── open_meteo.py   # ฟรี สภาพอากาศปัจจุบัน/ย้อนหลัง
│   ├── terrain/
│   │   └── srtm.py         # DEM 30 ม. → elevation/peak
│   └── _normalize.py       # NormalizedRow {lat, lon, time, metric, value, src} + converters
├── core/
│   ├── geometry.py         # bbox / point-in-polygon / grid / haversine
│   └── cache.py            # JSON/SQLite cache (key: src:metric:bbox:time)
├── analysis/
│   ├── indices.py          # NDVI/NDWI/NDBI (reuse geo/indices)
│   ├── landcover.py        # GFM ONNX Prithvi (reuse geo/landcover)
│   ├── change.py           # change detection 2 ช่วง (reuse geo/greenchange)
│   └── correlation.py      # Pearson cross/time + scatter (reuse geo/analysis)
├── agent/                  # สมอง (reuse เดิม + ขยาย)
│   ├── planner.py          # rule + LLM hybrid
│   ├── registry.py / tools.py / memory.py / llm.py
│   └── tools/              # met, satellite, terrain, crop, correlation
├── api/
│   ├── routes.py / schemas.py / errors.py
│   └── services.py         # เตรียม data_points/layer/chart จากผล tool
├── benchmark/
│   ├── tasks.py            # นิยามโจทย์ + ground-truth
│   └── metrics.py          # r/p/R²/RMSE/accuracy
├── static/ templates/      # frontend (ภายหลัง)
└── tests/
```

> งาน /geo, /agent เดิมถูกดึงขึ้นใช้ (reuse) ไม่ทิ้ง — โครงใหม่เป็น "จัดชั้น" ให้ตรงสถาปัตยกรรม

## 2. NormalizedRow (schema กลาง)

```python
@dataclass(frozen=True)
class NormalizedRow:
    lat: float; lon: float; time: str   # ISO date
    metric: str        # e.g. "hotspot_frp", "s2_ndvi", "power_t2m", "cams_pm25"
    value: float
    src: str           # e.g. "gistda", "firms", "nasa_power", "open_meteo", "cams_eac4"
    meta: dict = {}    # extras (satellite, confidence, ฯลฯ)
```
**ผลจากนี้:** spatial join + correlation + เปรียบเทียบเวลา = แค่ลูปบนแถวชุดเดียวกัน (ไม่ต้องรู้ว่าใครเป็นใคร)

## 3. API spec (เป้าหมาย)

| Method/Path | Params | กลับ | งาน |
|---|---|---|---|
| `GET /api/layers` | — | list metadata ของ layer ที่มี | 07 |
| `GET /api/layers/<name>` | `bbox, time, res` | GeoJSON FeatureCollection | 07 |
| `POST /api/correlation` | `{metric_a, metric_b, bbox, start, end, lag?}` | `{r, p, n, scatter_png, summary}` | 09 |
| `POST /api/query` | `{text}` | `{reply, data_points[], layers[], chart?, error}` | 18 |
| `GET /api/elevation?bbox=` | bbox | `{peak:[{rank,lat,lon,elev}]}` | 12 |
| `GET /api/benchmark` | — | สรุปผล benchmark | 22 |

**Job ตัวอย่าง `POST /api/query`:**
```json
{"text":"จุดไฟในเชียงใหม่ กับอุณหภูมิวันนั้น สัมพันธ์กันไหม"}
→ {"reply":"...", "data_points":[{lat,lon,value,metric}...],
   "layers":["hotspot_frp","power_t2m"],
   "chart":{"type":"scatter","r":0.42,"p":0.01,"points":[...]}}
```

## 4. เส้นทางข้อมูล (flux หลัก)

```
POST /api/query ─▶ agent.plan(text) ─▶ tools:
   met_query ──▶ datasources/met/nasa_power ─▶ NormalizedRow ─┐
   satellite_query ─▶ datasources/satellite/gistda ─▶ rows ─┼─▶ api/services
   correlation(metric_a,metric_b) ─▶ analysis/correlation ──┘   ▶ data_points + layer + chart
   (ถ้ามีภาพ) raster pixel layer ─▶ analysis/indices|change ─▶ pixel layer
```

## 5. ผิดพลาด/ขอบเขตที่ต้องจัดการ
- missing data (ฝั่งฟรีมีจุดขาด) → ทำ NaN/mask ให้ชัดก่อน correlation
- correlation ≠ causation → ทุกผลโชว์ข้อจำกัด
- ภาพต้อง co-registered (change layer)
- อัตราการ fetch จำกัด → cache ทุก adapter + rate-limit friendly (single flight)