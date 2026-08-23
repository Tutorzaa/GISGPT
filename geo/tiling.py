"""geo.tiling — ตัดภาพเป็น patch ขนาดคงที่ (224×224) และปะกลับหลังอนุมาน

โมเดล ViT (Prithvi) รับภาพขนาดคงที่ patch = 224×224 ภาพดาวเทียมใหญ่กว่ามาก
จึงต้องเลื่อนหน้าต่าง (sliding window) แล้วนำผลมารวมกัน
"""
import numpy as np

PATCH = 224
STRIDE = 112  # overlap 50%


def tile(arr, size=PATCH, stride=STRIDE):
    """คืน (patches, positions) โดย patches[i] รูปทรง (size,size,C)."""
    H, W = arr.shape[:2]
    patches, positions = [], []
    for y in range(0, H, stride):
        for x in range(0, W, stride):
            y1 = min(y + size, H)
            x1 = min(x + size, W)
            patch = arr[y:y1, x:x1]
            if patch.shape[0] < size or patch.shape[1] < size:
                pad = np.zeros((size, size) + arr.shape[2:], dtype=arr.dtype)
                pad[: patch.shape[0], : patch.shape[1]] = patch
                patch = pad
            patches.append(patch)
            positions.append((y, x, y1, x1))
    return patches, positions


def stitch(class_patches, positions, shape, size=PATCH):
    """รวม class map ราย patch กลับเป็นภาพเต็ม (เฉลี่ยบริเวณที่ซ้อนกัน)."""
    H, W = shape
    out = np.zeros((H, W), dtype="float32")
    cnt = np.zeros((H, W), dtype="float32")
    for patch, (y, x, y1, x1) in zip(class_patches, positions):
        h, w = y1 - y, x1 - x
        out[y:y1, x:x1] += patch[:h, :w]
        cnt[y:y1, x:x1] += 1
    out = np.where(cnt > 0, out / cnt, 0)
    return out.astype("int32")
