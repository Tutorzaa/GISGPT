"""config — โหลดค่าตั้งจาก .env + ค่าคงที่แพ็กเกจ (Ticket 01)

ใช้กับทุก data adapter / analysis / api แทนการอ่าน .env เองในแต่ละไฟล์
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
OUTPUTS = os.path.join(BASE_DIR, "outputs")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")

# โหลด .env (ไม่ทับ env ที่ตั้งไว้แล้ว) — โลจิกลอกตาม main.py เดิม แต่มารวมที่เดียว
_ENV = os.path.join(BASE_DIR, ".env")


def load_env(env_path=_ENV):
    """อ่าน key=value ในไฟล์ .env ลง os.environ (setdefault)."""
    if not os.path.exists(env_path):
        return
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def get(key, default=None):
    """ดึง env value (โหลด .env อัตโนมัติล่าช้า)."""
    load_env()
    return os.environ.get(key, default)


def ensure_dirs():
    for d in (DATA_RAW, OUTPUTS, CACHE_DIR):
        os.makedirs(d, exist_ok=True)
    return {"data_raw": DATA_RAW, "outputs": OUTPUTS, "cache": CACHE_DIR}


if __name__ == "__main__":
    print(ensure_dirs())
    print("firms_key=", "SET" if get("FIRMS_KEY") else "none")