from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "dataset_hash",
    "claim_verdict",
    "stability_score",
    "perturbation_parameters",
}

PROHIBITED_TERMS = {
    "diagnostic",
    "clinically proven",
    "clinical validation",
    "FDA approved",
    "patient diagnosis",
    "treatment recommendation",
}


def validate_report(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        errors.append(f"{path}: missing required fields: {', '.join(missing)}")

    text = json.dumps(data).lower()
    for term in sorted(PROHIBITED_TERMS):
        if term.lower() in text:
            errors.append(f"{path}: prohibited term found: {term}")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts")
    reports = sorted(root.rglob("report.json")) if root.exists() else []
    if not reports:
        print("No report.json files found.")
        return 0

    errors: list[str] = []
    for report in reports:
        errors.extend(validate_report(report))

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Validated {len(reports)} report(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
