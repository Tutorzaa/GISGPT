# GISGPT Prototype

> 📌 นี่คือ **prototype เดิม** (Leaflet chat demo) — ระบบปัจจุบันคือ Flask agent app (`main.py`)
> + Web GIS platform (`platform/`) ดู [README](../README.md)

## Files

```
prototype/
├── index.html          — responsive functional web prototype (entry point)
├── css/
│   └── style.css       — all styles (extracted from index.html)
├── js/
│   └── app.js          — all map/chat logic (extracted from index.html)
└── assets/
    ├── gisgpt-logo.png              — loading/logo screen
    └── GISGPT_Figma_Starter.svg     — monochrome desktop + mobile starter frames for import into Figma
```

## Prototype functions

Prototype functions
- GISGPT loading screen
- Satellite imagery (Esri World Imagery)
- Search place / coordinates via OpenStreetMap Nominatim
- Fly-to search result
- Rectangle ROI selection
- Custom ROI width/height
- ROI area estimate
- Chat panel: desktop drawer / mobile bottom sheet
- 5 demo analysis scenarios
- Mock analysis highlights on the selected ROI
- Zoom, layer switch, location, reset

Note: This is a level-2 prototype. Analysis results are simulated; they are not computer-vision results from the satellite imagery.
The map/search use public web services and therefore need an internet connection.
