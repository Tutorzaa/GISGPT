"""ทดสอบสัญญา tool แบบใหม่ (Ticket 03): data_points / layers / chart รวมเข้ากับ reply."""
from agent import Agent, memory


def make_agent():
    return Agent()


class TestComposeContract:
    def test_aggregates_new_fields(self):
        a = make_agent()
        ctx = {"history": []}   # handle() จะ setdefault history เสมอ
        res = a._compose([
            {"text": "พบ 2 จุด", "data_points": [{"lat": 1, "lon": 2}, {"lat": 3, "lon": 4}],
             "layers": ["hotspot"], "chart": {"r": 0.5}},
            {"text": "และอีก", "data_points": [{"lat": 5, "lon": 6}]},
        ], ctx)
        assert len(res["data_points"]) == 3
        assert res["layers"] == ["hotspot"]
        assert res["chart"] == [{"r": 0.5}]

    def test_reply_joins_texts(self):
        a = make_agent()
        res = a._compose([{"text": "ก"}, {"text": "ข"}], {"history": []})
        assert res["reply"] == "ก\n\nข"

    def test_legacy_result_yields_empty_new_fields(self):
        a = make_agent()
        res = a._compose([{"text": "เดิม", "artifacts": [{"type": "image", "url": "/o.png"}]}],
                         {"history": []})
        assert res["data_points"] == [] and res["layers"] == [] and res["chart"] == []

    def test_missing_text_becomes_fallback(self):
        a = make_agent()
        res = a._compose([{"data_points": [{"lat": 0, "lon": 0}]}], {"history": []})
        assert "ไม่เข้าใจคำสั่ง" in res["reply"]