"""agent.planner — ตัววางแผนแบบ rule-based (ตีความภาษาไทย/อังกฤษ)

สัญญา (contract) เดียวกับ LLMPlanner:
    plan(message, ctx) -> list[{"name": str, "args": dict}]

keyword ที่รู้จัก:
- classify  : จำแนก land cover
- index     : NDVI/NDWI/NDBI
- stats     : สถิติพื้นที่ (เฮกตาร์/ตร.กม.)
- explain   : อธิบายคลาส/สี
- list      : แสดงภาพที่อัปโหลด
- export    : ส่งออกผลลัพธ์
- help      : รายการความสามารถ
"""

_CLASSIFY = ["จำแนก", "landcover", "land cover", "land-cover", "classif", "ประเภทพื้นผิว", "แผนที่ปกคลุม"]
_INDEX = ["ndvi", "ndwi", "ndbi", "ดัชนี", "ดรรชนี", "index"]
_STATS = ["สถิติ", "พื้นที่", "เปอร์เซ็น", "เปอร์เซ็นต์", "เท่าไหร่", "เท่าไร", "กี่", "area", "stat", "เฮกตาร์", "ไร่", "ตาราง"]
_EXPLAIN = ["อธิบาย", "คลาส", "สี", "legend", "คือ", "หมายถึง", "แปล", "อะไร"]
_LIST = ["ภาพ", "ไฟล์", "upload", "มีอะไร", "แสดง", "รูป"]
_EXPORT = ["export", "ดาวน์โหลด", "save", "บันทึก", "geotiff", "tif", "ส่งออก"]
_HELP = ["ช่วย", "help", "ทำอะไร", "ความสามารถ", "อะไรได้บ้าง", "วิธีใช้", "ใช้ยังไง"]


def _hit(msg, keys):
    return any(k in msg for k in keys)


class RulePlanner:
    def plan(self, message, ctx=None):
        msg = message.lower()
        calls = []

        if _hit(msg, _CLASSIFY):
            calls.append({"name": "classify", "args": {}})

        if _hit(msg, _INDEX):
            which = "ndvi"
            for w in ("ndwi", "ndbi", "ndvi"):
                if w in msg:
                    which = w
                    break
            calls.append({"name": "index", "args": {"which": which}})

        if _hit(msg, _STATS):
            calls.append({"name": "stats", "args": {}})

        if _hit(msg, _EXPLAIN):
            calls.append({"name": "explain", "args": {}})

        if _hit(msg, _LIST):
            calls.append({"name": "list_images", "args": {}})

        if _hit(msg, _EXPORT):
            calls.append({"name": "export", "args": {"fmt": "geotiff"}})

        if not calls:
            calls.append({"name": "help", "args": {}})
        return calls
