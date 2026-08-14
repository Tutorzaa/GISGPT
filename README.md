# GISGPT

**GISGPT** is an AI-powered geographic chatbot that combines satellite imagery, GIS, and AI. Users can select an area on a map, ask questions in natural language, and receive geographic insights with visual highlights for buildings, roads, water, green spaces, and land use.

## Repository structure

```
GISGPT/
├── prototype/          — the web prototype (open prototype/index.html in a browser)
│   ├── index.html      — entry point
│   ├── css/style.css   — styles
│   ├── js/app.js       — map/chat logic
│   └── assets/         — images, Figma starter files
├── notebooks/          — Jupyter notebooks for satellite imagery analysis (learning path)
├── docs/
│   ├── PROTOTYPE.md    — prototype details and feature list
│   └── satellite-data.md — where to get free satellite imagery
└── requirements.txt    — Python dependencies for the notebooks
```

## Getting started with satellite analysis

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01-intro-satellite-analysis.ipynb
```
