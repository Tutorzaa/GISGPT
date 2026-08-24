"""benchmark.metrics — เมตริกวัดผล benchmark (Ticket 21)"""
from __future__ import annotations

import numpy as np


def rmse(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def r2(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    ss_res = np.sum((a - b) ** 2)
    ss_tot = np.sum((a - np.mean(a)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def accuracy(labels, preds) -> float:
    labels = np.asarray(labels)
    preds = np.asarray(preds)
    return float((labels == preds).mean()) if len(labels) else 0.0