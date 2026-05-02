from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .claim import find_prohibited_terms


DISCLAIMER = (
    "SubtypeLab outputs are for research support and hypothesis generation only. "
    "They are not for patient care or treatment decisions."
)


def generate_report(audit_result: dict[str, Any], output_root: Path) -> dict[str, Any]:
    required = ["dataset_hash", "claim_text", "stability_score", "verdict", "per_type_scores"]
    missing = [field for field in required if field not in audit_result]
    if missing:
        raise ValueError(f"Cannot generate report; missing fields: {', '.join(missing)}")

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "disclaimer": DISCLAIMER,
        "dataset_hash": audit_result["dataset_hash"],
        "claim_text": audit_result["claim_text"],
        "normalization_variant": audit_result.get("normalization_variant", "z-score"),
        "perturbation_parameters": audit_result.get("perturbation_parameters", {}),
        "stability_score": audit_result["stability_score"],
        "per_perturbation_scores": audit_result["per_type_scores"],
        "claim_verdict": audit_result["verdict"],
        "warnings": audit_result.get("warnings", []),
        "artifact_links": audit_result.get("artifact_links", []),
        "top_biomarkers": audit_result.get("biomarkers", []),
    }
    validate_report(report)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = output_root / str(audit_result["dataset_hash"])[:12] / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "report.json"
    html_path = report_dir / "report.html"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(_report_html(report), encoding="utf-8")

    report["paths"] = {
        "json": str(json_path),
        "html": str(html_path),
    }
    return report


def validate_report(report: dict[str, Any]) -> None:
    required = [
        "dataset_hash",
        "claim_verdict",
        "stability_score",
        "perturbation_parameters",
    ]
    missing = [field for field in required if field not in report]
    if missing:
        raise ValueError(f"Report is missing required fields: {', '.join(missing)}")

    text = json.dumps(report)
    prohibited = find_prohibited_terms(text)
    if prohibited:
        raise ValueError(f"Report contains prohibited terms: {', '.join(prohibited)}")


def _report_html(report: dict[str, Any]) -> str:
    rows = "\n".join(
        f"<tr><td>{feature['feature']}</td><td>{feature['robustness_score']:.3f}</td>"
        f"<td>{feature['baseline_score']:.3f}</td><td>{feature['one_run_artifact']}</td></tr>"
        for feature in report.get("top_biomarkers", [])
    )
    score_rows = "\n".join(
        f"<li>{kind}: {score:.3f}</li>"
        for kind, score in report.get("per_perturbation_scores", {}).items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SubtypeLab Reproducibility Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #172026; }}
    code {{ background: #eef2f4; padding: 0.1rem 0.25rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    td, th {{ border: 1px solid #d9e0e4; padding: 0.45rem; text-align: left; }}
  </style>
</head>
<body>
  <h1>SubtypeLab Reproducibility Report</h1>
  <p>{report["disclaimer"]}</p>
  <p><strong>Claim:</strong> {report["claim_text"]}</p>
  <p><strong>Verdict:</strong> {report["claim_verdict"]}</p>
  <p><strong>Stability score:</strong> {report["stability_score"]:.3f}</p>
  <p><strong>Dataset hash:</strong> <code>{report["dataset_hash"]}</code></p>
  <h2>Perturbation Scores</h2>
  <ul>{score_rows}</ul>
  <h2>Top Biomarkers</h2>
  <table>
    <thead><tr><th>Feature</th><th>Robustness</th><th>Baseline score</th><th>One-run artifact</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
