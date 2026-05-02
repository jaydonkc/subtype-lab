from __future__ import annotations

from math import comb

import numpy as np


def adjusted_rand_index(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    if len(labels_true) != len(labels_pred):
        raise ValueError("Label arrays must have the same length.")
    n = len(labels_true)
    if n < 2:
        return 1.0

    true_values, true_inverse = np.unique(labels_true, return_inverse=True)
    pred_values, pred_inverse = np.unique(labels_pred, return_inverse=True)
    contingency = np.zeros((len(true_values), len(pred_values)), dtype=int)
    for i in range(n):
        contingency[true_inverse[i], pred_inverse[i]] += 1

    sum_comb_cells = sum(comb(int(v), 2) for v in contingency.ravel() if v >= 2)
    row_sums = contingency.sum(axis=1)
    col_sums = contingency.sum(axis=0)
    sum_comb_rows = sum(comb(int(v), 2) for v in row_sums if v >= 2)
    sum_comb_cols = sum(comb(int(v), 2) for v in col_sums if v >= 2)
    total_pairs = comb(n, 2)
    expected_index = (sum_comb_rows * sum_comb_cols) / total_pairs if total_pairs else 0.0
    max_index = 0.5 * (sum_comb_rows + sum_comb_cols)
    denominator = max_index - expected_index
    if denominator == 0:
        return 1.0
    return float((sum_comb_cells - expected_index) / denominator)
