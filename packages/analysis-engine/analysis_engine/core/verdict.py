from __future__ import annotations


def compute_stability_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return float(sum(scores) / len(scores))


def compute_verdict(stability_score: float) -> str:
    if stability_score >= 0.75:
        return "robust"
    if stability_score >= 0.50:
        return "suspicious"
    return "fragile"
