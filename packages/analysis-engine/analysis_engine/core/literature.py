from __future__ import annotations

import json
import re
import ssl
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi


PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_CONTEXT = "cancer subtype biomarker"
MAX_LIMIT = 10
REQUEST_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class LiteratureHit:
    title: str
    journal: str
    year: str
    authors: list[str]
    url: str
    source: str = "PubMed"


@dataclass(frozen=True)
class LiteratureEvidence:
    marker: str
    context: str
    query: str
    source: str
    status: str
    evidence_level: str
    total_hits: int
    works_examined: int
    summary: str
    caveats: list[str]
    hits: list[LiteratureHit]

    def payload(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "hits": [asdict(hit) for hit in self.hits],
        }


def search_literature(marker: str, context: str = DEFAULT_CONTEXT, limit: int = 5) -> dict[str, Any]:
    marker = clean_marker(marker)
    context = clean_context(context)
    limit = max(1, min(MAX_LIMIT, limit))
    if is_synthetic_demo_marker(marker):
        return synthetic_demo_evidence(marker, context)
    query = build_pubmed_query(marker, context)

    try:
        pmids, total_hits = pubmed_search(query, limit)
        summaries = pubmed_summaries(pmids) if pmids else []
    except Exception as exc:
        return LiteratureEvidence(
            marker=marker,
            context=context,
            query=query,
            source="PubMed E-utilities",
            status="unavailable",
            evidence_level="unavailable",
            total_hits=0,
            works_examined=0,
            summary="Public literature lookup is currently unavailable. The biomarker audit is still usable, but prior-research evidence was not refreshed.",
            caveats=[f"Lookup failed: {exc}"],
            hits=[],
        ).payload()

    evidence_level = classify_evidence(total_hits)
    return LiteratureEvidence(
        marker=marker,
        context=context,
        query=query,
        source="PubMed E-utilities",
        status="ok",
        evidence_level=evidence_level,
        total_hits=total_hits,
        works_examined=len(summaries),
        summary=summarize_evidence(marker, context, total_hits, evidence_level),
        caveats=[
            "Literature evidence maps prior mentions; it does not validate the marker biologically or clinically.",
            "Use this as a triage signal before reading the papers and validating in independent cohorts.",
        ],
        hits=summaries,
    ).payload()


def clean_marker(marker: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "", marker.strip())
    if not cleaned:
        raise ValueError("Marker is required.")
    if len(cleaned) > 40:
        raise ValueError("Marker is too long.")
    return cleaned


def clean_context(context: str) -> str:
    words = re.findall(r"[A-Za-z0-9-]+", context or DEFAULT_CONTEXT)
    cleaned = " ".join(words[:12])
    return cleaned or DEFAULT_CONTEXT


def is_synthetic_demo_marker(marker: str) -> bool:
    return bool(re.fullmatch(r"GENE_\d{3}", marker))


def synthetic_demo_evidence(marker: str, context: str) -> dict[str, Any]:
    return LiteratureEvidence(
        marker=marker,
        context=context,
        query="not run for synthetic demo feature",
        source="SubtypeLab synthetic demo guardrail",
        status="demo_only",
        evidence_level="demo_synthetic",
        total_hits=0,
        works_examined=0,
        summary=f"{marker} is a synthetic demo feature, not a real marker symbol. Public literature lookup was skipped.",
        caveats=[
            "Synthetic demo features are generated for reproducibility testing only.",
            "Upload real marker names before using literature evidence for research triage.",
        ],
        hits=[],
    ).payload()


def build_pubmed_query(marker: str, context: str) -> str:
    return f"{marker}[Title/Abstract] AND ({context})"


def pubmed_search(query: str, limit: int) -> tuple[list[str], int]:
    params = urlencode(
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(limit),
            "sort": "relevance",
        }
    )
    payload = fetch_json(f"{PUBMED_BASE}/esearch.fcgi?{params}")
    result = payload.get("esearchresult", {})
    return result.get("idlist", []), int(result.get("count", 0))


def pubmed_summaries(pmids: list[str]) -> list[LiteratureHit]:
    params = urlencode(
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
    )
    payload = fetch_json(f"{PUBMED_BASE}/esummary.fcgi?{params}")
    result = payload.get("result", {})
    hits: list[LiteratureHit] = []
    for pmid in result.get("uids", []):
        item = result.get(pmid, {})
        title = strip_markup(item.get("title", "Untitled publication"))
        authors = [author.get("name", "") for author in item.get("authors", [])[:3] if author.get("name")]
        hits.append(
            LiteratureHit(
                title=title,
                journal=item.get("fulljournalname") or item.get("source") or "Unknown journal",
                year=str(item.get("pubdate", ""))[:4] or "n.d.",
                authors=authors,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )
        )
    return hits


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "SubtypeLab/0.1 literature-evidence"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def strip_markup(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value)).strip()


def classify_evidence(total_hits: int) -> str:
    if total_hits >= 25:
        return "known"
    if total_hits >= 5:
        return "emerging"
    if total_hits > 0:
        return "sparse"
    return "underexplored"


def summarize_evidence(marker: str, context: str, total_hits: int, evidence_level: str) -> str:
    if evidence_level == "known":
        return f"{marker} appears frequently in PubMed for this context ({total_hits} matching records). Treat it as a known or well-studied marker before claiming novelty."
    if evidence_level == "emerging":
        return f"{marker} has several matching PubMed records for this context ({total_hits}). It may be an emerging or context-dependent candidate."
    if evidence_level == "sparse":
        return f"{marker} has limited PubMed coverage for this context ({total_hits} matching records). Review the papers before treating it as novel."
    return f"No direct PubMed records were found for {marker} with context '{context}'. If the dataset evidence is strong, this may be an underexplored hypothesis."
