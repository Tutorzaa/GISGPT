"""geo.pipeline — รวมขั้นตอนวิเคราะห์เป็นฟังก์ชันเดียวให้ agent เรียกใช้

run_classification: จำแนก land cover (ใช้ ONNX Prithvi ถ้ามี ไม่งั้น baseline)
run_index: คำนวณดัชนีสเปกตรัม (NDVI/NDWI/NDBI) แล้วออกภาพ
"""
import os
import uuid

from . import indices
from . import io
from . import visualize
from .landcover import LandcoverONNX, find_model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS = os.path.join(BASE_DIR, "outputs")


def _ensure_outputs():
    os.makedirs(OUTPUTS, exist_ok=True)


def _make_preview(arr, path):
    """ภาพ RGB preview ย่อขนาด (สูงสุด ~1024 px) เพื่อแสดงในแชท."""
    H, W = arr.shape[:2]
    scale = max(1, H // 1024, W // 1024)
    img = visualize.rgb_preview(arr[::scale, ::scale])
    img.save(path)


def run_classification(path, file_id=None):
    """จำแนก land cover → คืน dict {class_map, classes, png, preview, stats, meta, mode}."""
    arr, meta = io.read_tiff(path)
    onnx_path, class_names = find_model()

    if onnx_path is not None and arr.shape[2] >= 6:
        model = LandcoverONNX(onnx_path, class_names)
        cls = model.predict(arr[..., :6])
        classes = model.classes
        mode = "prithvi"
    else:
        cls = indices.baseline_classify(arr)
        classes = indices.BASELINE_CLASSES
        mode = "baseline"

    _ensure_outputs()
    fid = file_id or uuid.uuid4().hex[:8]
    png = os.path.join(OUTPUTS, f"{fid}_landcover.png")
    preview = os.path.join(OUTPUTS, f"{fid}_preview.png")
    visualize.render_class_png(cls, classes, png)
    _make_preview(arr, preview)

    area = io.pixel_area_m2(meta)
    stats = visualize.class_stats(cls, classes, area)
    return dict(
        class_map=cls,
        classes=classes,
        png="/outputs/" + os.path.basename(png),
        preview="/outputs/" + os.path.basename(preview),
        stats=stats,
        meta=meta,
        mode=mode,
        pixel_area_m2=area,
    )


def run_index(path, which="ndvi", file_id=None):
    """คำนวณดัชนีสเปกตรัม → dict {url, which}."""
    arr, meta = io.read_tiff(path)
    val = {"ndvi": indices.ndvi, "ndwi": indices.ndwi, "ndbi": indices.ndbi}[which](arr)
    _ensure_outputs()
    fid = file_id or uuid.uuid4().hex[:8]
    png = os.path.join(OUTPUTS, f"{fid}_{which}.png")
    visualize.render_index_png(val, which, png)
    return dict(url="/outputs/" + os.path.basename(png), which=which)
