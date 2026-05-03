# How SubtypeLab Uses Kiro

SubtypeLab uses Kiro as the workflow-control layer for a deterministic bioinformatics application. Kiro is not used to invent biological conclusions. Instead, Kiro helps specify, enforce, and operate a reproducible claim-auditing workflow.

## Vibe Coding

The project started from a narrow product question:

> Can we build a crash-test lab for cancer subtype and biomarker claims?

The early Kiro conversations were structured around a small demo path: load synthetic expression data, enter a subtype claim, run baseline clustering, run perturbation stress tests, and produce a robust / suspicious / fragile verdict. Later iterations deliberately pushed the project beyond "agent with extra prompting" by adding uploaded datasets, optional metadata alignment, quality warnings, deterministic report artifacts, and MCP tools that call the same analysis engine as the web app.

The most useful generated code was the first full-stack scaffold: FastAPI analysis service, React/Vite UI, deterministic analysis modules, and local artifact/report generation.

## Spec-Driven Development

The `.kiro/specs/subtype-lab/` directory contains:

- `requirements.md`
- `design.md`
- `tasks.md`

The requirements define testable behavior around dataset loading, quality metrics, claim parsing, baseline analysis, perturbation audits, verdict thresholds, biomarker ranking, report generation, MCP tools, hooks, and local setup.

Compared with pure vibe coding, the spec forced clearer boundaries:

- verdicts must come from computed metrics
- demo data must be synthetic and deterministic
- audit jobs must expose progress
- uploaded metadata must align to sample IDs or fail clearly
- reports must include reproducibility evidence
- clinical language must be blocked

## Steering Docs

The steering docs live in `.kiro/steering/`:

- `product.md`
- `tech.md`
- `scientific-guardrails.md`
- `reproducibility.md`

The most important strategy was separating product ambition from scientific authority. The steering docs repeatedly tell Kiro:

- do not invent biomarker claims
- do not present demo results as validated biology
- deterministic tools own normalization, clustering, perturbations, scoring, and verdicts
- reports must include dataset hash, parameters, perturbation scores, and artifact paths
- the tool is for research support only

This made Kiro more useful because it generated code and documentation around a reproducible workflow instead of overclaiming biology.

## Agent Hooks

The repo includes Kiro hook configs under `.kiro/hooks/`:

- `run-analysis-tests.json`
- `validate-report.json`

The intended workflow:

- When analysis engine files change, Kiro runs the backend test suite.
- When report artifacts change, Kiro validates required report fields and checks for prohibited clinical language.

These hooks turn the scientific guardrails into executable workflow checks. They are important because the core risk in a bioinformatics AI project is not syntax; it is unsupported interpretation.

## MCP

The local MCP server lives in `packages/kiro-mcp-server/` and is configured in `.kiro/settings/mcp.json`.

It exposes deterministic tools:

- `inspect_dataset`
- `run_normalization`
- `run_subtyping`
- `run_perturbation_suite`
- `rank_robust_biomarkers`
- `audit_biological_claim`
- `explain_verdict`
- `generate_agent_findings`
- `generate_reproducibility_report`

MCP is the key Kiro feature for this project. It lets Kiro call real bioinformatics functions instead of producing freeform analysis prose. For example, Kiro can inspect the synthetic demo dataset or a local CSV/TSV file path, run deterministic subtyping, execute the perturbation suite, rank biomarkers, and generate reports. This makes the system auditable: Kiro can orchestrate and explain, but the verdict comes from code.

The web app also exposes this split directly after an audit. A Kiro explanation card summarizes the completed audit artifact, names the threshold used, highlights the weakest perturbation, and lists next checks. The card is Kiro-shaped explanation, not a second verdict engine.

The research-agent findings panel adds the discovery layer: it reads the completed audit artifact, checks top markers against PubMed evidence levels, computes a research-gap score, and returns cautious findings such as known robust markers, underexplored robust candidates, weak stress-test areas, or artifact risks. If `OPENAI_API_KEY` is configured, the same evidence snapshot can be passed through structured AI generation; without a key, the deployed demo uses the deterministic local agent fallback.

## Kiro Powers

SubtypeLab now includes a first-party Kiro Power at the repository root:

- `POWER.md`
- `mcp.json`
- `steering/scientific-guardrails.md`
- `steering/research-agent-workflow.md`

This lets the repo be installed from Kiro's Powers panel as a custom power. The power activates on bioinformatics, biomarker, cancer subtype, SNP, literature, perturbation, or reproducibility tasks and loads the same MCP server used by the local Kiro integration.

The power does not make Kiro the scientific authority. It packages the guardrails and tools so Kiro can call deterministic analysis functions, generate Kiro-guided explanations, and produce research-agent findings from computed evidence.

## Why This Is Kiro-Native

SubtypeLab is not just an app that was written with an AI assistant. The repo keeps Kiro artifacts at the root, uses Kiro specs as the implementation contract, uses steering docs to constrain scientific behavior, uses hooks for report/test validation, and exposes deterministic tools through MCP.

The final product is a working web app, but the development workflow is intentionally Kiro-shaped.
