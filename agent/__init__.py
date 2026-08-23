"""agent — สมองของ GISGPT

สถาปัตยกรรมแบบ hybrid:
- RulePlanner (agent/planner.py)  — ตีความภาษาไทย/อังกฤษด้วย keyword ทำงาน offline
- LLMPlanner  (agent/llm.py)       — สมอง LLM จริง ใช้เมื่อตั้ง HF_TOKEN (สัญญาเดียวกัน)
- Registry    (agent/registry.py)  — ลงทะเบียนเครื่องมือ (tools) ที่เรียกได้
- memory      (agent/memory.py)    — บริบทต่อ session
"""
from . import llm
from . import memory
from .planner import RulePlanner
from .registry import Registry
from .tools import register_tools


class Agent:
    def __init__(self):
        self.registry = Registry()
        register_tools(self.registry)
        self.rule_planner = RulePlanner()
        self.llm_planner = llm.LLMPlanner() if llm.available() else None

    def _plan(self, message, ctx):
        # hybrid: ลอง LLM ก่อน ถ้ามี token แล้วค่อยถอยกลับมา rule-based
        if self.llm_planner is not None:
            try:
                calls = self.llm_planner.plan(message, ctx)
                if calls:
                    return calls
            except Exception:
                pass
        return self.rule_planner.plan(message, ctx)

    def handle(self, sid, message):
        ctx = memory.get(sid)
        ctx.setdefault("history", []).append({"role": "user", "text": message})

        calls = self._plan(message, ctx)
        results = []
        for call in calls:
            tool = self.registry.get(call["name"])
            if tool is None:
                continue
            try:
                results.append(tool.func(ctx, **call.get("args", {})))
            except Exception as e:  # ไม่ให้ tool หนึ่งพังทั้งแชท
                results.append({"text": f"⚠️ เครื่องมือ '{call['name']}' ผิดพลาด: {e}"})

        return self._compose(results, ctx)

    def _compose(self, results, ctx):
        texts, artifacts, legend = [], [], None
        for r in results:
            if not r:
                continue
            if r.get("text"):
                texts.append(r["text"])
            artifacts.extend(r.get("artifacts") or [])
            d = r.get("data")
            if d and d.get("classes"):
                legend = [
                    {"id": k, "th": v["th"], "en": v["en"], "color": v["color"]}
                    for k, v in d["classes"].items()
                ]
        reply = "\n\n".join(texts) or "ไม่เข้าใจคำสั่ง — ลองถาม 'ช่วยด้วย' ดู"
        ctx["history"].append({"role": "assistant", "text": reply})
        return {"reply": reply, "artifacts": artifacts, "legend": legend}
