"""agent.memory — หน่วยความจำต่อ session (ภาพปัจจุบัน, ผลล่าสุด, ประวัติแชท)"""
from collections import defaultdict

MEMORY = defaultdict(dict)


def get(sid):
    return MEMORY[sid]
