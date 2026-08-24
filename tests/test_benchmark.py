"""ทดสอบ benchmark (Ticket 20–22) — synthetic tasks ควร recover ค่าที่รู้ได้"""
from benchmark import metrics as bm
from benchmark import tasks as bt


class TestMetrics:
    def test_rmse(self):
        assert bm.rmse([1, 2, 3], [1, 2, 3]) == 0.0
        assert bm.rmse([0, 0, 0], [1, 1, 1]) > 0.9

    def test_accuracy(self):
        assert bm.accuracy([1, 0, 1, 1], [1, 0, 1, 0]) == 0.75


class TestRunTasks:
    def test_synthetic_tasks_pass(self):
        results = bt.run_tasks([bt.task_linear_recovery, bt.task_no_correlation,
                                bt.task_timeseries_trend])
        for r in results:
            assert r["passed"], r["id"]

    def test_real_hotspot_signal(self):
        r = bt._eval(bt.task_real_hotspot_signal)
        assert r["measured_n"] > 0  # มีจุดจริงในฤดูเผา

    def test_runner_returns_consistent_shape(self):
        results = bt.run_tasks()
        for r in results:
            assert "id" in r and "passed" in r