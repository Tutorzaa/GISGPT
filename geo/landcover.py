"""geo.landcover — อนุมาน land cover ผ่านโมเดล ONNX (Prithvi ที่ fine-tune แล้ว)

โมเดล ONNX ได้จาก Colab notebook `02_finetune_landcover_colab.ipynb`:
- input : (B=1, T=1, C=6, H=224, W=224) float32, reflectance 0–1
- output: (1, num_classes, 224, 224) logits ต่อพิกเซล (semantic segmentation)
วางไฟล์ `<ชื่อ>.onnx` กับ `<ชื่อ>_classes.json` ไว้ใน models/ แล้วแอปจะใช้ทันที
"""
import json
import os

import numpy as np

from . import indices as idx
from . import tiling

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# จานสี default — คลาส land cover 7 ประเภท (Sen4Map, สไตล์ ESA WorldCover)
DEFAULT_CLASSES_7 = {
    0: {"th": "เกษตร", "en": "agriculture", "color": "#FFFF4C"},
    1: {"th": "ป่า", "en": "forest", "color": "#1D632F"},
    2: {"th": "ทุ่งหญ้า", "en": "grassland", "color": "#A6D854"},
    3: {"th": "ไม้พุ่ม", "en": "shrubland", "color": "#7A87C6"},
    4: {"th": "พื้นที่ชุ่มน้ำ", "en": "wetland", "color": "#E6953C"},
    5: {"th": "น้ำ", "en": "water", "color": "#1f77b4"},
    6: {"th": "เมือง/สิ่งก่อสร้าง", "en": "urban", "color": "#D62728"},
}

_PALETTE = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0"]


def find_model():
    """หาไฟล์ .onnx ตัวแรกใน models/ คืน (onnx_path, class_names) หรือ (None, None)."""
    if not os.path.isdir(MODELS_DIR):
        return None, None
    for f in sorted(os.listdir(MODELS_DIR)):
        if f.endswith(".onnx"):
            onnx_path = os.path.join(MODELS_DIR, f)
            return onnx_path, _load_class_names(onnx_path)
    return None, None


def _load_class_names(onnx_path):
    """โหลด class_names จากไฟล์ JSON ข้าง ๆ ไฟล์ .onnx."""
    base = os.path.splitext(onnx_path)[0]
    for cand in (base + "_classes.json", base + ".class_names.json"):
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as fh:
                raw = json.load(fh)
            return _normalize_classes(raw)
    return None


def _normalize_classes(raw):
    """รับ JSON เป็น dict {id:{th,en,color}} หรือ list[{id,th,en,color}] → dict {int:...}."""
    out = {}
    if isinstance(raw, list):
        for item in raw:
            i = int(item["id"])
            out[i] = {"th": item.get("th", f"คลาส {i}"), "en": item.get("en", f"class {i}"),
                      "color": item.get("color", _PALETTE[i % len(_PALETTE)])}
    elif isinstance(raw, dict):
        for k, v in raw.items():
            i = int(k)
            if isinstance(v, str):
                out[i] = {"th": v, "en": v, "color": _PALETTE[i % len(_PALETTE)]}
            else:
                out[i] = {"th": v.get("th", f"คลาส {i}"), "en": v.get("en", f"class {i}"),
                          "color": v.get("color", _PALETTE[i % len(_PALETTE)])}
    return out


class LandcoverONNX:
    """รันโมเดล ONNX (Prithvi head) บน CPU ด้วย onnxruntime."""

    def __init__(self, onnx_path, class_names=None):
        import onnxruntime as ort

        self.sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name
        self.num_classes = self.sess.get_outputs()[0].shape[1]
        if class_names:
            self.classes = class_names
        elif self.num_classes == 7:
            self.classes = dict(DEFAULT_CLASSES_7)
        else:
            self.classes = {
                i: {"th": f"คลาส {i}", "en": f"class {i}", "color": _PALETTE[i % len(_PALETTE)]}
                for i in range(self.num_classes)
            }

    def predict(self, arr):
        """arr รูปทรง (H,W,6) reflectance → class map (H,W) int32."""
        arr = idx.to_reflectance(arr)
        H, W = arr.shape[:2]
        patches, positions = tiling.tile(arr, size=224, stride=112)
        class_patches = []
        for p in patches:
            x = p.transpose(2, 0, 1)[None, None].astype("float32")  # (1,1,6,224,224)
            logits = self.sess.run(None, {self.input_name: x})[0]  # (1,C,224,224)
            class_patches.append(np.argmax(logits[0], axis=0))  # (224,224)
        return tiling.stitch(class_patches, positions, (H, W), size=224)
