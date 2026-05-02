# SubtypeLab

SubtypeLab is a local-first bioinformatics claim-auditing tool for cancer subtype and biomarker workflows. Given a gene-expression-style dataset and a claim like "these samples form three stable subtypes," the app runs deterministic stress tests and returns a verdict: `robust`, `suspicious`, or `fragile`.

The project is built for the Kiro hackathon's **Intellectual Pursuit Track**. Kiro is used as the workflow-control layer through specs, steering docs, hooks, and an MCP server that exposes deterministic analysis tools.

## Quick Start

```bash
docker compose up --build
```

Then open:

- Web UI: `http://localhost:3000`
- Analysis API: `http://localhost:8000/healthz`

If ports are already in use:

```bash
WEB_PORT=3001 ANALYSIS_ENGINE_PORT=8001 docker compose up --build
```

## Local Development Without Docker

Backend:

```bash
PYTHONPATH=packages/analysis-engine uvicorn analysis_engine.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Tests:

```bash
PYTHONPATH=packages/analysis-engine pytest packages/analysis-engine/tests
```

## Demo Workflow

1. Load the synthetic demo dataset.
2. Select or edit the claim: "These samples form three stable subtypes."
3. Run the baseline analysis.
4. Run the claim audit.
5. Review the stability verdict, perturbation scores, PCA projection, biomarker table, and exported report path.

The synthetic dataset is deterministic and contains no real patient data.

## Kiro Integration

The repo keeps Kiro artifacts at the root:

- `.kiro/specs/subtype-lab/requirements.md`
- `.kiro/specs/subtype-lab/design.md`
- `.kiro/specs/subtype-lab/tasks.md`
- `.kiro/steering/*.md`
- `.kiro/hooks/*.json`
- `.kiro/settings/mcp.json`

The MCP server exposes tools such as `inspect_dataset`, `run_subtyping`, `run_perturbation_suite`, `rank_robust_biomarkers`, `audit_biological_claim`, and `generate_reproducibility_report`.

## Research Boundary

SubtypeLab is for research support and hypothesis generation. It does not provide clinical validation, patient diagnosis, or treatment recommendations.
