"""agent.llm — ตัววางแผนด้วย LLM (hybrid สมองที่สอง)

ใช้ Hugging Face Inference API (endpoint แบบ OpenAI-compatible) เมื่อตั้ง HF_TOKEN
ใน environment variable — ถ้าไม่ตั้งก็คืน available() = False แล้ว agent ถอยไปใช้
RulePlanner แทน โค้ดฝั่งนี้จึงไม่พังแม้ไม่มี token/ไม่มีเน็ต

สัญญาเดียวกับ RulePlanner: plan(message, ctx) -> list[{"name","args"}]
"""
import json
import os

import requests

_SYSTEM = """คุณคือตัววางแผนของ GISGPT (geospatial agent)
หน้าที่: แปลงคำขอผู้ใช้เป็นรายการเครื่องมือที่จะเรียก ตาม JSON schema นี้เท่านั้น
{"calls":[{"name":str,"args":dict}]}

เครื่องมือที่มี:
- classify      : จำแนก land cover จากภาพดาวเทียม (ไม่มี args)
- index         : คำนวณดัชนีสเปกตรัม args={"which":"ndvi|ndwi|ndbi"}
- stats         : สถิติพื้นที่รายคลาส (ไม่มี args)
- explain       : อธิบายคลาสและสี (ไม่มี args)
- list_images   : แสดงภาพที่อัปโหลด (ไม่มี args)
- export        : ส่งออกผลลัพธ์ args={"fmt":"geotiff"}
- help          : แสดงความสามารถ (ไม่มี args)

ตัวอย่าง:
ผู้ใช้ "จำแนก land cover แล้วบอกพื้นที่" -> {"calls":[{"name":"classify","args":{}},{"name":"stats","args":{}}]}
ผู้ใช้ "คำนวณ NDWI" -> {"calls":[{"name":"index","args":{"which":"ndwi"}}]}
ตอบเฉพาะ JSON ไม่ต้องอธิบายเพิ่ม
"""


def available():
    return bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"))


class LLMPlanner:
    def __init__(self, model="Qwen/Qwen2.5-7B-Instruct"):
        self.model = model
        self.token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        self.url = "https://router.huggingface.co/v1/chat/completions"

    def plan(self, message, ctx=None):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": message},
            ],
            "temperature": 0.0,
            "max_tokens": 256,
        }
        r = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        text = text.strip().strip("```").strip("json").strip("```").strip()
        data = json.loads(text)
        return data.get("calls")
