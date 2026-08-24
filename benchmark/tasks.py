"""benchmark.tasks — โจทย์ประเมิน (ground-truth ที่รู้ค่า) + runner (Ticket 20–21)

งานทั้งหมดใช้ข้อมูลจำลองที่ "คำตอบจริง" ชัดเจน → รันผ่าน analysis pipeline
=> วัดว่าเครื่องมือวิเคราะห์คืนผลใกล้ความจริงแค่ไหน (ได้ค่า r/R²/RMSE)
"""
from __future__ import annotations

import numpy as np

from analysis import correlation as corr
from benchmark import metrics as _m
from core.normalize import make


# ---------------- task definitions (แต่ละอันมี ground truth) ----------------
def _build_cross_rows(x, y):
    """สร้าง NormalizedRow คู่ (a=x, b=y) ที่พิกัด/วันเดียวกัน."""
    rows_a, rows_b = [], []
    for i, (xi, yi) in enumerate(zip(x, y)):
        rows_a.append(make(10 + i * 0.1, 100.0, "2023-04-05", "f_a", float(xi), "src_a"))
        rows_b.append(make(10 + i * 0.1, 100.0, "2023-04-05", "f_b", float(yi), "src_b"))
    return rows_a, rows_b


def task_linear_recovery(n=40, seed=7):
    """y = 0.8x + noise → ควรรีคัฟ r ≈ 0.8."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 10, n)
    y = 0.8 * x + rng.normal(0, 0.6, n)
    res = corr.cross_sectional(*_build_cross_rows(x, y), metric_a="f_a", metric_b="f_b")
    return {
        "id": "corr_linear_recovery",
        "name": "Cross-sectional: recover known r=0.8 from noisy data",
        "kind": "regression",
        "ground_truth_r": 0.8,
        "measured_r": res["r"], "p": res["p"], "n": res["n"],
        "pass": lambda self: abs(self["measured_r"] - 0.8) < 0.25,
    }


def task_no_correlation(n=40, seed=11):
    """x, y เป็นอิสระ → r ควร ≈ 0."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 10, n)
    y = rng.uniform(0, 10, n)
    res = corr.cross_sectional(*_build_cross_rows(x, y), metric_a="f_a", metric_b="f_b")
    return {
        "id": "corr_noise_recovery",
        "name": "Cross-sectional: independent data → r ≈ 0",
        "kind": "regression",
        "ground_truth_r": 0.0,
        "measured_r": res["r"], "p": res["p"], "n": res["n"],
        "pass": lambda self: abs(self["measured_r"]) < 0.35,
    }


def task_timeseries_trend(n_days=15, seed=3):
    """อนุกรมรายวัน: B = 2*A + 1 → time-series r ≈ 1."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(20, 30, n_days)
    b = 2.0 * a + rng.normal(0, 0.5, n_days)
    da = [make(15.0, 100.0, f"2023-04-{d + 1:02d}", "p_a", float(v), "sa") for d, v in enumerate(a)]
    db = [make(15.0, 100.0, f"2023-04-{d + 1:02d}", "p_b", float(v), "sb") for d, v in enumerate(b)]
    res = corr.time_series(da, db, metric_a="p_a", metric_b="p_b")
    return {
        "id": "timeseries_linear",
        "name": "Time-series: daily trend recovers r≈1",
        "kind": "regression",
        "ground_truth_r": 1.0,
        "measured_r": res["r"], "p": res["p"], "n": res["n"],
        "pass": lambda self: self["measured_r"] > 0.9,
    }


def task_real_hotspot_signal():
    """Spotlight real data: hotspot (GISTDA) ในช่วงฤดูเผา (เม.ย.) ต้องมีจุดจริง (n>0)."""
    from datasources import gistda

    bbox = [102.6, 14.4, 103.4, 15.4]
    rows = gistda.hotspot_rows(bbox, use_cache=True)
    return {
        "id": "real_hotspot_presence",
        "name": "Real data: hotspots present in burning season (Buriram Apr)",
        "kind": "detection",
        "ground_truth_n": ">0",
        "measured_n": len(rows),
        "pass": lambda self: self["measured_n"] > 0,
    }


TASKS = [task_linear_recovery, task_no_correlation, task_timeseries_trend, task_real_hotspot_signal]


def _eval(fn) -> dict:
    r = fn()
    r["passed"] = bool(r["pass"](r) if callable(r["pass"]) else r["pass"])
    r.pop("pass", None)
    return r


def run_tasks(tasks=None) -> list[dict]:
    """รันทุกโจทย์ → รายการผล (ลบ lambda pass, เพิ่ม passed)."""
    out = []
    for fn in (tasks or TASKS):
        try:
            out.append(_eval(fn))
        except Exception as e:
            out.append({"id": getattr(fn, "__name__", "?"), "error": str(e), "passed": False})
    return out