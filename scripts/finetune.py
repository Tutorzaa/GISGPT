"""scripts/finetune.py — Fine-tune Prithvi-EO-2.0-300M สำหรับ land cover (per-pixel)

สร้างโมเดล ONNX ที่แอป GISGPT ใช้ได้พอดี:
- input : (B=1, T=1, C=6, H=224, W=224) float32, reflectance 0–1
- output: (1, num_classes, 224, 224) logits ต่อพิกเซล

ข้อมูล: Sen4Map (train.h5/val.h5 จาก https://datapub.fz-juelich.de/sen4map/)
แปลง: ใช้เฟรมแรกของ time series + 6 แบนด์ (B,G,R,NIR,SWIR1,SWIR2) + label ของ patch
      ขยายเป็น per-pixel (label ทั้ง patch = คลาสของ patch)

รันบน Colab (GPU):
    python finetune.py --train train.h5 --val val.h5 --subset 8000 --epochs 8 --push peeradon4778/prithvi-landcover-th

โหมดทดสอบ pipeline (ไม่มี GPU/ข้อมูลจริง — สร้างข้อมูลจำลองเอง):
    python finetune.py --synthetic --epochs 2
"""
import argparse
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

# ลำดับแบนด์ 6 ช่อง ที่ตรงกับแอป (geo/landcover.py) — HLS order
BANDS6 = ["BLUE", "GREEN", "RED", "NIR_BROAD", "SWIR_1", "SWIR_2"]

# คลาส land cover ของ Sen4Map (10 คลาส LUCAS 2018)
CLASS_NAMES = [
    {"th": "พืชไร่", "en": "arable land", "color": "#FFFF4C"},
    {"th": "ทุ่งหญ้า", "en": "grassland", "color": "#A6D854"},
    {"th": "ไม้ผล/ไม้ยืนต้น", "en": "permanent crops", "color": "#FFAA00"},
    {"th": "ป่าใบกว้าง", "en": "broadleaf forest", "color": "#1D632F"},
    {"th": "ป่าสน", "en": "coniferous forest", "color": "#2A7A42"},
    {"th": "พื้นที่ชุ่มน้ำ", "en": "wetland", "color": "#E6953C"},
    {"th": "น้ำ", "en": "water", "color": "#1f77b4"},
    {"th": "เมือง/สิ่งก่อสร้าง", "en": "urban", "color": "#D62728"},
    {"th": "พื้นที่เปิด/ทราย/หิน", "en": "bare", "color": "#B3B3B3"},
    {"th": "อื่น ๆ", "en": "other", "color": "#7A7A7A"},
]


# --------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------
class LandCoverDataset(Dataset):
    """อ่าน Sen4Map h5 → เฟรมแรก, 6 แบนด์, resize 224, label per-pixel."""

    def __init__(self, h5_path, subset=None, size=224, seed=0, max_memory_gb=6):
        import h5py

        self.size = size
        with h5py.File(h5_path, "r") as f:
            print("🔍 โครงสร้าง h5:", {k: f[k].shape for k in f.keys()})
            imgs, labels = self._resolve(f)
            if subset:
                rng = np.random.default_rng(seed)
                idx = rng.choice(len(imgs), min(subset, len(imgs)), replace=False)
                imgs, labels = imgs[idx], labels[idx]
        print(f"📦 โหลด {len(imgs)} ตัวอย่าง รูป {imgs.shape}")

        # เลือกเฟรมแรก + 6 แบนด์ (สมมุติ layout (N, T, C, H, W))
        x = imgs[:, 0, :6]  # (N, 6, H, W)
        self.x = torch.from_numpy(self._to_float(x)).float()
        self.y = torch.from_numpy(labels).long()

    def _resolve(self, f):
        """หา key ของภาพ/ป้าย — รองรับชื่อหลายแบบ แล้ว print ให้ดู."""
        img_key = next((k for k in f.keys() if "image" in k.lower()), None)
        lab_key = next((k for k in f.keys() if "label" in k.lower()), None)
        if img_key is None or lab_key is None:
            raise RuntimeError(
                f"หา key images/labels ไม่เจอ — keys ในไฟล์คือ {list(f.keys())}\n"
                "เปิด notebook แล้วปรับโค้ดส่วน _resolve ให้ตรงกับโครงสร้างจริง"
            )
        imgs = f[img_key][:]
        labels = f[lab_key][:]
        if labels.ndim > 1:
            labels = labels.reshape(labels.shape[0])
        return imgs, labels

    def _to_float(self, arr):
        arr = np.asarray(arr, dtype="float32")
        if arr.max() > 2.0:  # HLS/S2 สเกล 0–10000 → 0–1
            arr = arr / 10000.0
        return np.clip(arr, 0, 1)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, i):
        img = F.interpolate(self.x[i][None], size=(self.size, self.size), mode="bilinear")[0]
        return img, self.y[i]


class SyntheticLandCover(Dataset):
    """ข้อมูลจำลอง 6 แบนด์ 4 คลาส — ใช้เทสต์ pipeline โดยไม่ต้องโหลดข้อมูลจริง."""

    def __init__(self, n=400, size=64, seed=0):
        rng = np.random.default_rng(seed)
        self.n, self.size = n, size
        sig = np.array(
            [
                [0.08, 0.10, 0.04, 0.02, 0.01, 0.01],  # น้ำ
                [0.05, 0.12, 0.05, 0.50, 0.15, 0.10],  # พืชพรรณ
                [0.10, 0.14, 0.20, 0.25, 0.32, 0.28],  # พื้นโล่ง
                [0.20, 0.22, 0.28, 0.22, 0.40, 0.36],  # สิ่งก่อสร้าง
            ],
            dtype="float32",
        )
        self.y = rng.integers(0, 4, n)
        self.x = np.zeros((n, 6, size, size), dtype="float32")
        for i in range(n):
            self.x[i] = sig[self.y[i]][:, None, None] * rng.uniform(0.9, 1.1, (6, 1, 1))

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        img = F.interpolate(torch.from_numpy(self.x[i])[None], size=(self.size, self.size))[0]
        return img, self.y[i]


# --------------------------------------------------------------------------
# โมเดล
# --------------------------------------------------------------------------
class _SegWrapper(torch.nn.Module):
    """รับ (B,T,C,H,W) หรือ (B,C,H,W) → logits (B,C,H,W)

    dict_input=True  → โมเดลสไตล์ terratorch (รับ {"image": ...})
    dict_input=False → CNN ธรรมดา (รับ tensor)
    """

    def __init__(self, model, dict_input=True):
        super().__init__()
        self.model = model
        self.dict_input = dict_input

    def forward(self, x):
        if x.dim() == 4:
            x = x.unsqueeze(1)  # (B,C,H,W) → (B,1,C,H,W)
        if self.dict_input:
            out = self.model({"image": x})
            return out["logits"] if isinstance(out, dict) else out
        return self.model(x[:, 0])  # ใช้เฟรมแรก (B,C,H,W)


class _TinyCNN(torch.nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Conv2d(6, 32, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(32, 64, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(64, num_classes, 1),
        )

    def forward(self, x):
        return self.net(x)


def build_model(num_classes=4):
    try:
        from terratorch.models import PrithviModelFactory

        model = PrithviModelFactory.build_model(
            task="segmentation",
            backbone="prithvi_eo_v2_300",
            decoder="UPerNetDecoder",
            in_channels=6,
            bands=BANDS6,
            num_frames=1,
            num_classes=num_classes,
            pretrained=True,
            backbone_pretrain_img_size=224,
            backbone_patch_size=16,
        )
        print("✅ โหลด Prithvi-EO-2.0-300M + UPerNet head จาก Hugging Face (terratorch)")
        return _SegWrapper(model, dict_input=True)
    except Exception as e:
        print("⚠️ terratorch โหลดไม่ได้:", e)
        print("→ ใช้โมเดล CNN เล็กแทน (ทดสอบ pipeline ได้ แต่ไม่ใช่ foundation model)")
        return _SegWrapper(_TinyCNN(num_classes), dict_input=False)


# --------------------------------------------------------------------------
# เทรน / ประเมิน
# --------------------------------------------------------------------------
def train(model, loader, epochs, lr=6e-5, device="cuda"):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.05)
    model.train()
    for ep in range(epochs):
        tot, corr, loss_sum = 0, 0, 0.0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)  # (B, C, H, W)
            target = y.view(-1, 1, 1).expand(-1, logits.shape[2], logits.shape[3])
            loss = F.cross_entropy(logits, target)
            opt.zero_grad()
            loss.backward()
            opt.step()
            pred = logits.argmax(1)
            tot += target.numel()
            corr += (pred == target).sum().item()
            loss_sum += loss.item()
        print(f"epoch {ep+1}/{epochs}  loss={loss_sum/len(loader):.4f}  acc={corr/tot*100:.2f}%")


def evaluate(model, loader, device="cuda"):
    model.eval()
    tot, corr = 0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x).argmax(1)
            target = y.view(-1, 1, 1).expand(-1, pred.shape[1], pred.shape[2])
            tot += target.numel()
            corr += (pred == target).sum().item()
    print(f"✅ val accuracy = {corr/tot*100:.2f}%")
    return corr / tot


# --------------------------------------------------------------------------
# export ONNX + push HF
# --------------------------------------------------------------------------
def export_onnx(model, out_path, patch=224, num_classes=4):
    model.eval()
    dummy = torch.randn(1, 1, 6, patch, patch)
    torch.onnx.export(
        model,
        dummy,
        out_path,
        input_names=["image"],
        output_names=["logits"],
        opset_version=17,
    )
    print(f"📦 ONNX: {out_path}  (input (1,1,6,{patch},{patch}) → output (1,{num_classes},{patch},{patch}))")
    return out_path


def push_hf(onnx_path, repo_id, token=None, num_classes=4):
    from huggingface_hub import HfApi, login

    if token:
        login(token)
    api = HfApi()
    api.create_repo(repo_id, exist_ok=True, repo_type="model")
    api.upload_file(
        path_or_fileobj=onnx_path, path_in_repo=os.path.basename(onnx_path), repo_id=repo_id
    )
    api.upload_file(
        path_or_fileobj=json.dumps(CLASS_NAMES[:num_classes], ensure_ascii=False),
        path_in_repo="class_names.json",
        repo_id=repo_id,
    )
    readme = (
        "# Prithvi Land Cover (GISGPT)\n"
        "Fine-tuned Prithvi-EO-2.0-300M → ONNX (6 bands, single frame, per-pixel)\n"
        "input (1,1,6,224,224) float32 reflectance 0-1 → output (1,{n},224,224)\n".format(n=num_classes)
    )
    api.upload_file(path_or_fileobj=readme, path_in_repo="README.md", repo_id=repo_id)
    print(f"🚀 push สำเร็จ: https://huggingface.co/{repo_id}")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Fine-tune Prithvi-EO-2.0 (land cover, per-pixel)")
    ap.add_argument("--train", help="path train.h5 (Sen4Map)")
    ap.add_argument("--val", help="path val.h5 (Sen4Map)")
    ap.add_argument("--synthetic", action="store_true", help="ใช้ข้อมูลจำลอง (เทสต์ pipeline)")
    ap.add_argument("--subset", type=int, default=None, help="สุ่มใช้เพียง N ตัวอย่าง")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--patch", type=int, default=224)
    ap.add_argument("--onnx", default="prithvi_landcover.onnx")
    ap.add_argument("--push", help="repo_id บน HF เช่น peeradon4778/prithvi-landcover-th")
    ap.add_argument("--cpu", action="store_true", help="บังคับ CPU (ไม่ใช้ GPU)")
    args = ap.parse_args()

    device = "cpu" if args.cpu else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ device = {device}")

    if args.synthetic or not (args.train and args.val):
        print("🧪 โหมดข้อมูลจำลอง (4 คลาส)")
        train_ds = SyntheticLandCover(n=800)
        val_ds = SyntheticLandCover(n=200, seed=1)
        num_classes = 4
    else:
        print("🌍 โหลด Sen4Map...")
        train_ds = LandCoverDataset(args.train, subset=args.subset, size=args.patch)
        val_ds = LandCoverDataset(args.val, subset=min(args.subset or 1000, 1000), size=args.patch)
        num_classes = 10

    train_ld = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0)
    val_ld = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=0)

    model = build_model(num_classes).to(device)
    train(model, train_ld, args.epochs, device=device)
    evaluate(model, val_ld, device=device)

    export_onnx(model, args.onnx, patch=args.patch, num_classes=num_classes)

    if args.push:
        push_hf(args.onnx, args.push, num_classes=num_classes)


if __name__ == "__main__":
    main()
