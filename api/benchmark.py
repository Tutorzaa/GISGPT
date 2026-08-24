"""api.benchmark_api — GET /api/benchmark (Ticket 22)

Run the spatio-temporal analysis benchmarks and return a summary + per-task metrics.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from benchmark.tasks import run_tasks

bp = Blueprint("benchmark_api", __name__)


@bp.get("/api/benchmark")
def benchmark():
    results = run_tasks()
    passed = sum(1 for r in results if r.get("passed"))
    return jsonify({
        "total": len(results),
        "passed": passed,
        "results": results,
        "note": ("Benchmark of the analysis pipeline (spatio-temporal relation recovery). "
                 "Ground-truth tasks are synthetic with known answers; more (GFM real) "
                 "models can be plugged in later."),
    })