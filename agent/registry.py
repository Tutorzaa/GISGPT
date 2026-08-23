"""agent.registry — ลงทะเบียนเครื่องมือ (tools) ที่ agent เรียกใช้ได้"""
from dataclasses import dataclass, field


@dataclass
class Tool:
    name: str
    description: str
    params: list
    func: object
    category: str = "general"


class Registry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        self._tools[tool.name] = tool
        return tool

    def get(self, name):
        return self._tools.get(name)

    def all(self):
        return list(self._tools.values())

    def describe(self):
        return [
            {"name": t.name, "description": t.description, "params": t.params, "category": t.category}
            for t in self._tools.values()
        ]
