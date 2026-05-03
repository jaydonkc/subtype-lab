---
name: "subtype-lab"
displayName: "SubtypeLab Bioinformatics Research Agent"
description: "Audit cancer subtype and biomarker claims with deterministic perturbation tests, literature evidence checks, and cautious research-agent findings."
keywords: ["bioinformatics", "biomarker", "cancer", "subtype", "SNP", "expression", "research agent", "literature", "PubMed", "perturbation", "reproducibility", "SubtypeLab"]
author: "SubtypeLab"
---

# SubtypeLab Power

SubtypeLab turns Kiro into a reproducible bioinformatics research copilot. Use this power when a task involves cancer subtyping, biomarker triage, SNP or omics hypothesis checks, literature evidence, perturbation testing, or research reproducibility.

The power must not invent biology. Kiro can orchestrate tools, summarize computed evidence, and suggest validation next steps, but deterministic code owns the verdict.

# Onboarding

## Step 1: Validate the local toolchain

From the repository root, confirm the Python analysis engine can import:

```bash
PYTHONPATH=packages/analysis-engine python3 -m compileall packages/analysis-engine/analysis_engine packages/kiro-mcp-server/mcp_server
```

If MCP dependencies are missing, install them locally:

```bash
python3 -m pip install -r packages/kiro-mcp-server/requirements.txt
```

## Step 2: Use the SubtypeLab MCP tools

This power includes an MCP server named `subtype-lab`. Prefer MCP tool calls over freeform reasoning for analysis work.

Important tools:

- `inspect_dataset`
- `run_normalization`
- `run_subtyping`
- `run_perturbation_suite`
- `rank_robust_biomarkers`
- `audit_biological_claim`
- `explain_verdict`
- `generate_agent_findings`
- `generate_reproducibility_report`

# Research-Agent Workflow

For subtype or biomarker questions:

1. Inspect the dataset first.
2. Parse the claim and run the deterministic claim audit.
3. Review perturbation stability before discussing biomarkers.
4. Rank robust biomarkers only after the claim audit is complete.
5. Generate agent findings from computed audit evidence.
6. Treat agent findings as research triage, not validation.
7. Recommend independent cohort validation for any promising marker.

# Guardrails

- Do not present synthetic demo markers as known biology.
- Do not imply diagnostic, treatment, FDA, or clinical-validation status.
- Do not change a robust / suspicious / fragile verdict with prose.
- If evidence is missing, say it is missing.
- Always mention dataset hash, normalization variant, seed, and perturbation scores when summarizing a result.

# When to Load Steering Files

- Scientific interpretation or biomarker wording -> `steering/scientific-guardrails.md`
- Research-agent finding generation -> `steering/research-agent-workflow.md`
- Reproducibility, reports, or audit artifacts -> `.kiro/steering/reproducibility.md`
- Product demo or hackathon narrative -> `.kiro/steering/product.md`
