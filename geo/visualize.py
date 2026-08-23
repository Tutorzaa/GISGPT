"""geo.visualize — ระบายสี class map, คำนวณสถิติพื้นที่, แปลงเป็น PNG"""
import numpy as np
from PIL import Image


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def render_class_png(cls_map, classes, path=None):
    """ระบายสี class map (H,W) เป็น PNG ตาม dict classes {id: {color, ...}}."""
    H, W = cls_map.shape
    rgb = np.zeros((H, W, 3), dtype="uint8")
    for k, meta in classes.items():
        color = meta["color"] if isinstance(meta, dict) else meta
        rgb[cls_map == int(k)] = hex_to_rgb(color)
    img = Image.fromarray(rgb)
    if path:
        img.save(path)
    return img


def class_stats(cls_map, classes, pixel_area_m2=None):
    """สถิติรายคลาส: จำนวนพิกเซล, % , พื้นที่ (m²/ha/km²)."""
    total = cls_map.size
    out = []
    for k, meta in classes.items():
        n = int((cls_map == int(k)).sum())
        area_m2 = n * pixel_area_m2 if pixel_area_m2 else None
        row = dict(
            class_id=int(k),
            label_th=meta["th"] if isinstance(meta, dict) else str(k),
            label_en=meta["en"] if isinstance(meta, dict) else str(k),
            color=meta["color"] if isinstance(meta, dict) else meta,
            pixels=n,
            pct=round(100.0 * n / total, 2),
        )
        if area_m2 is not None:
            row.update(
                area_m2=round(area_m2, 2),
                area_ha=round(area_m2 / 10000.0, 3),
                area_km2=round(area_m2 / 1e6, 5),
            )
        out.append(row)
    return out


def render_index_png(val, which, path=None):
    """วาดดัชนีสเปกตรัมเป็น PNG ด้วย matplotlib colormap (Agg backend)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cmap = {"ndvi": "RdYlGn", "ndwi": "Blues", "ndbi": "OrRd"}.get(which, "viridis")
    plt.imsave(path, val, cmap=cmap, vmin=-1, vmax=1)
    return path


def rgb_preview(arr):
    """สร้างภาพ RGB preview (สำหรับแสดงภาพต้นฉบับ) — คัด 3 แบนด์แรก."""
    a = arr[..., :3].astype("float32")
    a = np.clip(a, 0, 1) if a.max() <= 1.0 else np.clip(a / 10000.0, 0, 1)
    rgb = (a * 255).astype("uint8")
    return Image.fromarray(rgb)
