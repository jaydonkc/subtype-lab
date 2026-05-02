from __future__ import annotations

from . import tools


try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - dependency is installed in Docker/Kiro env
    raise SystemExit(
        "The SubtypeLab MCP server requires the 'mcp' package. "
        "Install packages/kiro-mcp-server/requirements.txt before running it."
    ) from exc


mcp = FastMCP("SubtypeLab")


@mcp.tool()
def inspect_dataset(dataset_id: str = "demo") -> dict:
    """Inspect a dataset and return dimensions, quality metrics, and hash."""

    return tools.inspect_dataset(dataset_id)


@mcp.tool()
def run_normalization(dataset_id: str = "demo", variant: str = "z-score") -> dict:
    """Run a deterministic normalization variant over a dataset."""

    return tools.run_normalization(dataset_id, variant)


@mcp.tool()
def run_subtyping(
    dataset_id: str = "demo",
    subtype_count: int = 3,
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    """Run deterministic k-means subtyping over a dataset."""

    return tools.run_subtyping(dataset_id, subtype_count, normalization_variant, seed)


@mcp.tool()
def run_perturbation_suite(
    dataset_id: str = "demo",
    subtype_count: int = 3,
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    """Run the deterministic perturbation suite and return stability scores."""

    return tools.run_perturbation_suite(dataset_id, subtype_count, normalization_variant, seed)


@mcp.tool()
def rank_robust_biomarkers(
    dataset_id: str = "demo",
    claim_text: str = "These samples form three stable subtypes.",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    """Rank biomarkers by robustness across perturbation runs."""

    return tools.rank_robust_biomarkers(dataset_id, claim_text, normalization_variant, seed)


@mcp.tool()
def audit_biological_claim(
    claim_text: str,
    dataset_id: str = "demo",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    """Audit a biological claim and return a computed verdict."""

    return tools.audit_biological_claim(claim_text, dataset_id, normalization_variant, seed)


@mcp.tool()
def generate_reproducibility_report(
    claim_text: str = "These samples form three stable subtypes.",
    dataset_id: str = "demo",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    """Generate a reproducibility report for a completed audit workflow."""

    return tools.generate_reproducibility_report(claim_text, dataset_id, normalization_variant, seed)


if __name__ == "__main__":
    mcp.run()
