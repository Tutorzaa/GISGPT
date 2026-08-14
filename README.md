# GISGPT

**GISGPT** is an AI-powered geographic chatbot that combines satellite imagery, GIS, and AI. Users can select an area on a map, ask questions in natural language, and receive geographic insights with visual highlights for buildings, roads, water, green spaces, and land use.

## Repository structure

```
GISGPT/
├── platform/            — GIS platform (OpenLayers): layer management, attribute tables,
│   │                       file import (GeoJSON/Shapefile/KML/GPX) — the path to a real GIS app
│   ├── index.html       — entry point (open in browser)
│   ├── css/style.css    — styles
│   ├── js/              — config, map, layers, import, table, main
│   └── README.md        — usage + roadmap
├── prototype/           — the original web prototype (Leaflet chat demo)
│   ├── index.html       — entry point
│   ├── css/style.css    — styles
│   ├── js/app.js        — map/chat logic
│   └── assets/          — images, Figma starter files
├── notebooks/           — Jupyter notebooks for satellite imagery analysis (learning path)
├── docs/
│   ├── PROTOTYPE.md     — prototype details and feature list
│   ├── satellite-data.md — where to get free satellite imagery
│   └── gistda-data.md   — GISTDA open data API guide (register key at api-gateway.gistda.or.th)
└── requirements.txt     — Python dependencies for the notebooks
```

## Getting started with satellite analysis

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01-intro-satellite-analysis.ipynb
```

## GISTDA data (Thai satellite/GIS data)

To use GISTDA's 2-meter satellite basemap and data APIs (rice, floods, PM2.5, ...):

1. Register a free API key at https://api-gateway.gistda.or.th
2. Put the key in `GISGPT.GISTDA_KEY` in `platform/js/config.js` (adds a GISTDA 2M basemap) and/or `GISTDA_KEY` in `prototype/js/app.js`
3. See `docs/gistda-data.md` and `notebooks/02-gistda-open-data.ipynb`
