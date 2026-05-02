from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "prohibited_terms.json"


@dataclass(frozen=True)
class ParsedClaim:
    claim_type: str
    subtype_count: int
    text: str


def load_prohibited_terms() -> list[str]:
    data = json.loads(CONFIG_PATH.read_text())
    return [str(term) for term in data["terms"]]


def find_prohibited_terms(text: str, terms: list[str] | None = None) -> list[str]:
    terms = terms or load_prohibited_terms()
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]


def validate_claim_language(text: str) -> None:
    matches = find_prohibited_terms(text)
    if matches:
        joined = ", ".join(matches)
        raise ValueError(f"Clinical interpretation language is not supported: {joined}.")


def parse_claim(text: str) -> ParsedClaim:
    validate_claim_language(text)
    normalized = text.strip()
    lower = normalized.lower()

    subtype_match = re.search(r"(\d+)\s+(?:stable\s+)?subtypes?", lower)
    if "subtype" in lower or "cluster" in lower:
        subtype_count = int(subtype_match.group(1)) if subtype_match else 3
        return ParsedClaim("subtype-count", subtype_count, normalized)

    if "biomarker" in lower or "gene" in lower or "distinguish" in lower:
        return ParsedClaim("biomarker-discrimination", 3, normalized)

    if "cohort" in lower or "stable" in lower:
        return ParsedClaim("cohort-stability", 3, normalized)

    raise ValueError(
        "Claim must describe subtypes, clusters, biomarkers, genes, cohorts, or stability."
    )
