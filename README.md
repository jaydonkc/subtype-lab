# SubtypeLab

SubtypeLab is a local-first bioinformatics claim-auditing tool for cancer subtype and biomarker workflows. Given a gene-expression-style dataset and a claim like "these samples form three stable subtypes," the app runs deterministic stress tests and returns a verdict: `robust`, `suspicious`, or `fragile`.

The project is built for the Kiro hackathon's **Intellectual Pursuit Track**. Kiro is used as the workflow-control layer through specs, steering docs, hooks, and an MCP server that exposes deterministic analysis tools.

This is not a clinical tool and not an AI interpretation wrapper. The UI and Kiro MCP layer orchestrate deterministic code for normalization, clustering, perturbation scoring, biomarker ranking, and report generation.

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

The Docker path is the intended judge-facing setup. The first build may take a few minutes while public base images and package dependencies are downloaded.

## Public Project URL

For hackathon submission, deploy the repo as a single Docker web service. The backend Docker image builds the web UI and serves both the React app and FastAPI routes from one URL. See [DEPLOYMENT.md](./DEPLOYMENT.md).

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

Frontend build:

```bash
cd apps/web
npm install
npm run build
```

Report validation:

```bash
python3 scripts/validate_report.py artifacts
```

## Demo Workflow

1. Load the synthetic demo dataset, or upload a CSV/TSV expression matrix with optional sample metadata.
2. Review quality metrics, warning flags, feature summaries, dataset hash, and the preview heatmap.
3. Select or edit the claim: "These samples form three stable subtypes."
4. Run the baseline analysis.
5. Review the PCA projection, top-variable feature heatmap, and baseline feature table.
6. Run the claim audit.
7. Review the stability verdict, perturbation scores, biomarker table, warnings, and exported report path.
8. Download the JSON or HTML reproducibility report.

The synthetic dataset is deterministic and contains no real patient data.

Expected demo story:

- The subtype claim should come back as a strong computed signal.
- The audit should still flag that some top candidate biomarkers are one-run artifacts.
- This shows the product's core value: a claim can be mostly robust while some downstream biomarkers remain fragile.

Uploaded expression matrices should use rows as samples and columns as features. A first column named `sample_id`, `sample`, `id`, or `index` is treated as the sample identifier. Optional metadata should include `sample_id`, or have the same row order as the expression matrix.

## Kiro Integration

The repo keeps Kiro artifacts at the root:

- `POWER.md`
- `mcp.json`
- `.kiro/specs/subtype-lab/requirements.md`
- `.kiro/specs/subtype-lab/design.md`
- `.kiro/specs/subtype-lab/tasks.md`
- `.kiro/steering/*.md`
- `.kiro/hooks/*.json`
- `.kiro/settings/mcp.json`

The repository root is also a custom Kiro Power. Install this repo from Kiro's Powers panel by GitHub URL or local path to load SubtypeLab's MCP tools and research-agent steering on demand.

The MCP server exposes tools such as `inspect_dataset`, `run_subtyping`, `run_perturbation_suite`, `rank_robust_biomarkers`, `audit_biological_claim`, `explain_verdict`, `generate_agent_findings`, and `generate_reproducibility_report`. `inspect_dataset` can inspect the built-in demo dataset or a local CSV/TSV file path. `explain_verdict` is the Kiro-facing explanation layer: it summarizes computed audit evidence without changing the metric-derived verdict. `generate_agent_findings` turns computed audit metrics, marker robustness, artifact flags, and literature evidence into cautious research findings.

See [KIRO_USAGE.md](./KIRO_USAGE.md) for the submission writeup.

## Verification Checklist

Before submission, run:

```bash
PYTHONPATH=packages/analysis-engine pytest packages/analysis-engine/tests
(cd apps/web && npm run build && npm audit --audit-level=moderate)
python3 scripts/validate_report.py artifacts
docker compose up --build
```

Then manually open `http://localhost:3000` and click through the full demo workflow.

## Troubleshooting

If `localhost:3000` or `localhost:8000` is already in use, override the ports:

```bash
WEB_PORT=3001 ANALYSIS_ENGINE_PORT=8001 docker compose up --build
```

If local Python imports fail outside Docker, set:

```bash
export PYTHONPATH=packages/analysis-engine
```

If report validation finds no reports, run a claim audit first.

## Research Boundary

SubtypeLab is for research support and hypothesis generation. It does not provide clinical validation, patient diagnosis, or treatment recommendations.

## Known Limitations

- The bundled dataset is synthetic.
- Job state is in memory and resets when the backend restarts.
- Reports are written to local disk under `artifacts/`.
- The UI is a focused hackathon workflow, not a complete lab information system.
- Results are not clinical evidence.
