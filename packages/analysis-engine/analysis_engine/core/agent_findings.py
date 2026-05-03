from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

from .literature import search_literature


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_CONTEXT = "cancer subtype biomarker"

FINDINGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["agentic_ai"]},
        "headline": {"type": "string"},
        "executive_summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "finding_type": {
                        "type": "string",
                        "enum": ["claim", "marker", "research_gap", "risk"],
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence": {"type": "string"},
                    "interpretation": {"type": "string"},
                    "recommended_next_step": {"type": "string"},
                },
                "required": [
                    "title",
                    "finding_type",
                    "confidence",
                    "evidence",
                    "interpretation",
                    "recommended_next_step",
                ],
                "additionalProperties": False,
            },
        },
        "agent_trace": {
            "type": "array",
            "items": {"type": "string"},
        },
        "guardrails": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["mode", "headline", "executive_summary", "findings", "agent_trace", "guardrails"],
    "additionalProperties": False,
}


def build_agent_findings(
    audit_result: dict[str, Any],
    marker_limit: int = 5,
    literature_limit: int = 3,
) -> dict[str, Any]:
    evidence = collect_agent_evidence(audit_result, marker_limit, literature_limit)
    fallback = build_deterministic_findings(evidence)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return fallback

    try:
        ai_findings = call_openai_findings(evidence, api_key)
        ai_findings["provider"] = "openai"
        ai_findings["model"] = os.environ.get("OPENAI_FINDINGS_MODEL", "gpt-4.1-mini")
        ai_findings["evidence_snapshot"] = evidence
        return ai_findings
    except Exception as exc:
        fallback["warnings"].append(f"AI findings provider failed; deterministic findings returned instead: {exc}")
        return fallback


def collect_agent_evidence(
    audit_result: dict[str, Any],
    marker_limit: int,
    literature_limit: int,
) -> dict[str, Any]:
    biomarkers = audit_result.get("biomarkers", [])[:marker_limit]
    context = context_from_claim(str(audit_result.get("claim_text", "")))
    marker_evidence = []
    for marker in biomarkers:
        feature = str(marker.get("feature", ""))
        if not feature:
            continue
        literature = search_literature(feature, context, literature_limit)
        marker_evidence.append(
            {
                "feature": feature,
                "robustness_score": float(marker.get("robustness_score", 0.0)),
                "baseline_score": float(marker.get("baseline_score", 0.0)),
                "one_run_artifact": bool(marker.get("one_run_artifact", False)),
                "literature": {
                    "status": literature.get("status"),
                    "evidence_level": literature.get("evidence_level"),
                    "total_hits": literature.get("total_hits", 0),
                    "summary": literature.get("summary", ""),
                    "top_titles": [hit.get("title", "") for hit in literature.get("hits", [])[:3]],
                },
                "research_gap_score": research_gap_score(marker, literature),
            }
        )

    return {
        "claim_text": audit_result.get("claim_text", ""),
        "dataset_id": audit_result.get("dataset_id", ""),
        "dataset_hash": audit_result.get("dataset_hash", ""),
        "verdict": audit_result.get("verdict", "unknown"),
        "stability_score": audit_result.get("stability_score", 0.0),
        "per_type_scores": audit_result.get("per_type_scores", {}),
        "warnings": audit_result.get("warnings", []),
        "normalization_variant": audit_result.get("normalization_variant", ""),
        "subtype_count": audit_result.get("subtype_count", 0),
        "marker_evidence": marker_evidence,
    }


def build_deterministic_findings(evidence: dict[str, Any]) -> dict[str, Any]:
    verdict = str(evidence.get("verdict", "unknown"))
    stability = float(evidence.get("stability_score", 0.0))
    markers = evidence.get("marker_evidence", [])
    top_gap = sorted(markers, key=lambda item: item["research_gap_score"], reverse=True)[:3]
    artifact_count = sum(1 for item in markers if item["one_run_artifact"])
    weakest_name, weakest_score = weakest_perturbation(evidence.get("per_type_scores", {}))

    findings = [
        {
            "title": f"Subtype claim is {verdict}",
            "finding_type": "claim",
            "confidence": "high" if stability >= 0.75 or stability < 0.5 else "medium",
            "evidence": f"Computed stability score is {stability:.3f}; verdict threshold returned {verdict}.",
            "interpretation": "The agent is summarizing deterministic audit evidence, not changing the scientific verdict.",
            "recommended_next_step": "Use the reproducibility report as the evidence record before deciding whether to validate in another cohort.",
        }
    ]
    if weakest_name:
        findings.append(
            {
                "title": "Weakest stress test needs review",
                "finding_type": "risk",
                "confidence": "medium",
                "evidence": f"{weakest_name.replace('_', ' ')} scored {weakest_score:.3f}.",
                "interpretation": "This perturbation is the most likely place for the claim to break under realistic dataset shifts.",
                "recommended_next_step": "Inspect this perturbation class before treating the subtype claim as stable.",
            }
        )
    if top_gap:
        findings.append(
            {
                "title": "Highest research-gap marker candidates",
                "finding_type": "research_gap",
                "confidence": "medium",
                "evidence": ", ".join(
                    f"{item['feature']} ({item['research_gap_score']}/100, {item['literature']['evidence_level']})"
                    for item in top_gap
                ),
                "interpretation": "These markers combine audit support with limited prior-literature signal, so they are better hypothesis leads than obvious known markers.",
                "recommended_next_step": "Prioritize independent-cohort validation for high-gap markers that are not one-run artifacts.",
            }
        )
    if artifact_count:
        findings.append(
            {
                "title": "Some marker candidates may be artifacts",
                "finding_type": "marker",
                "confidence": "high",
                "evidence": f"{artifact_count} of {len(markers)} reviewed markers were flagged as one-run artifacts.",
                "interpretation": "These markers looked important in one pass but did not consistently survive perturbation runs.",
                "recommended_next_step": "Down-rank artifact-flagged markers until they replicate across perturbations or another cohort.",
            }
        )

    return {
        "mode": "deterministic_agent",
        "provider": "local",
        "model": "rules+literature",
        "headline": f"Research agent findings: {verdict} claim, {len(findings)} evidence-backed findings.",
        "executive_summary": (
            "SubtypeLab generated a research triage summary from computed audit metrics, marker robustness, "
            "artifact flags, and PubMed evidence levels. No clinical claims are made."
        ),
        "findings": findings,
        "agent_trace": [
            "Read completed audit artifact.",
            "Checked top markers against PubMed evidence levels.",
            "Scored research gaps from marker robustness, literature coverage, and artifact flags.",
            "Generated cautious findings constrained to the computed evidence.",
        ],
        "guardrails": guardrails(),
        "warnings": list(evidence.get("warnings", [])),
        "evidence_snapshot": evidence,
    }


def call_openai_findings(evidence: dict[str, Any], api_key: str) -> dict[str, Any]:
    payload = {
        "model": os.environ.get("OPENAI_FINDINGS_MODEL", "gpt-4.1-mini"),
        "instructions": (
            "You are a cautious bioinformatics research-synthesis agent. Generate JSON findings only from the supplied "
            "audit evidence. Do not invent biology, do not imply clinical validation, and do not recommend diagnosis or treatment. "
            "Focus on robust claims, fragile claims, marker artifacts, research gaps, and next validation checks."
        ),
        "input": json.dumps(evidence, separators=(",", ":")),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "agent_findings",
                "strict": True,
                "schema": FINDINGS_SCHEMA,
            }
        },
        "max_output_tokens": 1800,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    return json.loads(extract_output_text(response_payload))


def extract_output_text(response_payload: dict[str, Any]) -> str:
    if response_payload.get("output_text"):
        return str(response_payload["output_text"])
    for item in response_payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return str(content["text"])
    raise ValueError("OpenAI response did not include output text.")


def research_gap_score(marker: dict[str, Any], literature: dict[str, Any]) -> int:
    robustness = float(marker.get("robustness_score", 0.0))
    artifact_penalty = 0.35 if marker.get("one_run_artifact") else 0.0
    literature_level = str(literature.get("evidence_level", "unavailable"))
    novelty = {
        "underexplored": 0.95,
        "sparse": 0.75,
        "emerging": 0.45,
        "known": 0.15,
        "unavailable": 0.35,
    }.get(literature_level, 0.35)
    score = max(0.0, min(1.0, (0.6 * robustness) + (0.4 * novelty) - artifact_penalty))
    return round(score * 100)


def weakest_perturbation(per_type_scores: dict[str, float]) -> tuple[str, float]:
    if not per_type_scores:
        return "", 0.0
    name = min(per_type_scores, key=per_type_scores.get)
    return name, float(per_type_scores[name])


def context_from_claim(claim_text: str) -> str:
    lower = claim_text.lower()
    if "subtype" in lower and "biomarker" in lower:
        return DEFAULT_CONTEXT
    if "subtype" in lower:
        return "cancer subtype gene expression"
    if "biomarker" in lower:
        return "cancer biomarker"
    return DEFAULT_CONTEXT


def guardrails() -> list[str]:
    return [
        "Findings are generated only from computed audit artifacts and public-literature evidence levels.",
        "The AI layer may summarize and prioritize; it may not change the deterministic verdict.",
        "No diagnostic, treatment, or clinical-validation claims are permitted.",
        "Every finding is a research hypothesis triage signal that requires independent validation.",
    ]
