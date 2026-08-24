"""benchmark — ชุดประเมินความสามารถวิเคราะห์เชิงพื้นที่-เวลา (Ticket 20–22)

โจทย์ (tasks) มี "คำตอบจริง" (ground truth) ที่รู้ค่า — ไล่ผ่าน analysis pipeline
เพื่อตรวจว่าเครื่องมือวิเคราะห์หา/คืนค่าตรงกับความจริงแค่ไหน
=> เป็นรากฐานวิจัย "verify ความเข้าใจโมเดล" จากข้อมูล (จะสลับใส่ GFM จริงภายหลัง)
"""
from . import metrics  # noqa: F401
from .tasks import TASKS, run_tasks  # noqa: F401