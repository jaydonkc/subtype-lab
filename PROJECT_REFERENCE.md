# Project Reference: SubtypeLab / BioClaim Auditor

## Working Concept

**SubtypeLab** is a focused bioinformatics claim-auditing tool for cancer subtyping and biomarker discovery. Given a dataset and a claim such as "these samples form three subtypes" or "these genes distinguish subtype A from subtype B," the system tries to break the claim with deterministic stress tests.

The core value is not normalization by itself. Normalization is only one attack surface. The product is a crash-test lab for subtype and biomarker claims: it checks whether a result survives noisy samples, missing features, cohort splits, normalization variants, and batch-like shifts.

The project should be framed as a research-support tool for hypothesis generation, not diagnosis or clinical decision-making.

## Current Recommendation

Build **one polished, narrow tool** instead of a broad AI bioinformatics platform.

Best MVP:

> Given a cancer expression dataset and candidate subtype labels or discovered clusters, SubtypeLab audits whether the subtype and biomarker signal is robust, fragile, or suspicious.

Avoid expanding v1 into SNP analysis, full multi-omics, paper-to-pipeline generation, broad convergent evolution, or clinical interpretation. Those can be future modules after the claim-auditing workflow works well.

## Hackathon Track

Primary track: **Intellectual Pursuit Track**

Social good angle: SubtypeLab helps students, small labs, and under-resourced research teams evaluate the reproducibility of bioinformatics findings before trusting fragile conclusions.

## Hackathon Stress Test

Realistic verdict: **potentially competitive, not automatically a winner**.

SubtypeLab can be a strong Kiro hackathon submission if the demo feels like a real lab QA tool instead of a dashboard around toy clustering. The judges need to understand the product in one sentence:

> SubtypeLab tries to break fragile cancer subtype and biomarker claims before researchers trust them.

The project is strongest when it is narrow, visual, and artifact-backed:

- upload or load demo data
- choose a subtype or biomarker claim
- run baseline analysis
- run the claim audit
- show robust / fragile / suspicious verdict
- show evidence plots and generated artifacts
- export a reproducible report
- show Kiro enforcing the workflow through specs, steering, hooks, and MCP

The project becomes weak if it expands into a broad "AI bioinformatics agent" or if the Kiro integration is only prompts and documentation.

## Expected Judging Fit

### Implementation

Target score potential: **16-19 / 20**

Strong if the repo includes:

- a working app that installs and runs consistently
- deterministic analysis engine
- local MCP server exposing real analysis tools
- `.kiro/specs/` with requirements, design, and tasks
- `.kiro/steering/` with scientific and reproducibility guardrails
- hooks that run tests, validate reports, or block unsupported scientific claims
- generated artifacts with dataset hash, parameters, metrics, and plots

Risk:

- If MCP and hooks are decorative, judges may view the project as an AI wrapper.
- If the app cannot run cleanly from the repo, the submission fails the functionality requirement regardless of concept quality.

### Innovation and Design

Target score potential: **14-18 / 20**

Strong if the UI makes the audit concept obvious:

- a clear claim input
- baseline result
- stress-test result
- verdict: robust, fragile, or suspicious
- stability charts and warnings
- heatmap or projection view
- exportable report

Risk:

- Generic clustering plots will look boring.
- The demo must feel like "we attacked this claim and found what survived," not "we ran a normal bioinformatics pipeline."

### Social Good

Target score potential: **13-17 / 20**

Strong if the pitch clearly explains the affected community:

- small labs
- students
- under-resourced research teams
- junior researchers learning reproducible computational biology

The social-good claim:

> Fragile biomarker and subtype claims can waste research time, sequencing budget, and follow-up experiments. SubtypeLab makes those risks visible earlier.

Risk:

- This is less immediately emotional than accessibility or wellness projects.
- The demo and writeup must make the practical harm obvious to non-bio judges.

## Submission Must-Haves

- Public open source repo.
- OSI-approved `LICENSE` visible at repo root.
- `.kiro/` directory committed at repo root.
- `.kiro/` and subfolders must not be in `.gitignore`.
- Source code, assets, demo data, and setup instructions included.
- One-command local run if possible.
- Functional app URL if deployed.
- Public demo video under 3 minutes.
- English text description and testing instructions.
- Clear category selection: **Intellectual Pursuit Track**.
- Kiro usage writeup covering specs, steering docs, hooks, MCP, and vibe-coding strategy.
- Only use demo/synthetic data or clearly licensed public data.
- Avoid third-party trademarks, copyrighted music, and unlicensed assets in the video.

## Winning Demo Path

The 3-minute video should show product behavior, not just slides:

1. Open the repo and briefly show `.kiro/`.
2. Show Kiro spec and steering docs in a few seconds.
3. Start the app.
4. Load the demo cancer-expression-style dataset.
5. Select the claim: "These samples form three stable subtypes."
6. Run baseline analysis.
7. Run claim audit.
8. Show that one candidate signal is fragile while another survives perturbations.
9. Export the reproducible report.
10. Show a Kiro hook warning/blocking unsupported clinical wording.

The key viewer takeaway should be:

> This tool does not ask AI to invent biology. It uses Kiro to plan, enforce, and orchestrate a deterministic scientific claim audit.

## Problem

Cancer subtyping and biomarker discovery workflows can produce convincing-looking results that fail under small changes in preprocessing, cohort composition, missing genes, batch effects, or noise. Researchers often see clean heatmaps or clusters before they know whether the signal is stable enough to trust.

The practical problem:

> Labs can waste time chasing fragile subtype or biomarker claims because the first analysis looks plausible.

SubtypeLab should help researchers audit claims before they present, publish, or build follow-up experiments around them.

## Product Promise

SubtypeLab answers one main question:

> If we try to break this biological claim, does it survive?

It helps answer:

- Do the same subtypes appear under different normalization choices?
- Do candidate biomarkers survive missing-gene and noisy-sample perturbations?
- Does batch-like noise create fake clusters?
- Which subtype assignments are stable across bootstrap runs?
- Which features are robust signals versus one-run artifacts?
- Are results robust, fragile, or suspicious?
- Which warnings should a researcher review before trusting the result?

## Lab Usefulness

This can be useful for a bioinformatics lab if the lab works with expression matrices, subtype labels, clustering, biomarkers, or cohort comparisons.

The lab-facing use case:

- Before someone says "we found three subtypes," the tool tests whether those subtypes survive perturbation.
- Before chasing candidate biomarkers, the tool shows which ones are stable versus one-run artifacts.
- Before a result goes into a slide deck or report, the tool generates reproducible evidence: parameters, plots, dataset hash, and robustness scores.
- For junior researchers, the tool makes common failure modes visible: batch-like effects, noisy samples, missing genes, unstable clusters, and overconfident interpretation.

This should be positioned as analysis QA, not as a replacement for proper statistical review.

## Why This Is Not Just an AI Wrapper

The valuable part of the system is the deterministic analysis engine:

- Dataset inspection and validation
- Clustering/subtyping
- Perturbation and bootstrap testing
- Stability scoring
- Biomarker robustness ranking
- Claim verdict generation from computed metrics
- Reproducible report generation

AI/Kiro should orchestrate, explain, and enforce workflow quality. It should not invent scientific results.

The product should have executable pieces that prompts cannot fake:

- deterministic analysis functions
- stored artifacts
- repeatable metrics
- test coverage
- hooks that block unsupported reports
- report validation

## MVP Workflow

1. User loads a demo gene-expression-style dataset or uploads a CSV/TSV feature matrix plus metadata.
2. User provides a claim or chooses an auto-generated claim:
   - "These samples form 3 subtypes."
   - "These genes distinguish subtype A from subtype B."
   - "These biomarkers are stable across cohorts."
3. The app validates the dataset and shows basic quality metrics.
4. The system runs or reruns the baseline subtype/biomarker analysis.
5. User runs the claim audit.
6. The system attacks the claim across perturbations:
   - missing features
   - noisy samples
   - cohort splits
   - normalization variants
   - batch-like shifts
7. The app displays:
   - claim verdict: robust, fragile, or suspicious
   - subtype stability score
   - cluster consistency chart
   - robust biomarker ranking
   - heatmap or PCA/UMAP-style projection
   - warning flags for fragile results
8. User exports a reproducible report with dataset hash, method parameters, plots, and generated artifacts.

## Kiro Integration Strategy

Kiro should be integrated as the development and workflow-control layer.

The writeup should explicitly explain that Kiro was used strategically:

- **Vibe coding** for early UI and workflow exploration.
- **Specs** for turning the idea into testable requirements, design, and implementation tasks.
- **Steering docs** for scientific guardrails and project conventions.
- **MCP** for giving Kiro executable bioinformatics tools instead of relying on generated prose.
- **Hooks** for validating reports, running tests, and catching unsupported clinical language.
- **Powers** only if there is enough time to package the reusable workflow cleanly.

### Specs

The repo should include `.kiro/specs/subtype-robustness/` with:

- `requirements.md`
- `design.md`
- `tasks.md`

The spec should define the analysis workflow in testable requirements, for example:

> When a user audits a subtype claim, the system shall perturb the dataset, rerun clustering, calculate subtype stability, rank biomarker robustness, and return a claim verdict backed by generated artifacts.

### Steering Docs

The repo should include `.kiro/steering/` files such as:

- `product.md`
- `tech.md`
- `scientific-guardrails.md`
- `reproducibility.md`

Important steering rules:

- The LLM must not invent biomarker claims.
- Scientific conclusions must cite generated artifacts.
- Deterministic tools own normalization, clustering, perturbation, and scoring.
- Reports must state that outputs are for research support, not diagnosis.
- Every analysis run must preserve parameters, dataset hash, and artifacts.
- Claim verdicts must be computed from metrics, not freeform model judgment.

### MCP Server

Build a local MCP server that exposes real analysis tools to Kiro:

- `inspect_dataset`
- `run_normalization`
- `run_subtyping`
- `run_perturbation_suite`
- `rank_robust_biomarkers`
- `audit_biological_claim`
- `generate_reproducibility_report`

Kiro can call these tools from the IDE, but the tools perform deterministic computation.

### Hooks

Kiro hooks should enforce workflow quality:

- Run tests when analysis engine files change.
- Validate report artifacts before final output.
- Warn or block unsupported language such as "diagnostic biomarker" or "clinically proven."
- Check that exported reports include dataset hash, method parameters, and artifact links.
- Block claim reports that do not include a computed verdict and metric evidence.

### Kiro Power

The reusable Kiro side is packaged as a first-party `SubtypeLab` power:

- `POWER.md`
- `mcp.json`
- research-agent steering
- scientific guardrails
- MCP access to deterministic analysis tools

This makes the project Kiro-native instead of merely Kiro-built: Kiro can activate the domain workflow, call the same MCP tools as the app, and keep scientific guardrails in context.

## Suggested Repo Shape

```text
repo/
  .kiro/
    specs/
      subtype-robustness/
        requirements.md
        design.md
        tasks.md
    steering/
      product.md
      tech.md
      scientific-guardrails.md
      reproducibility.md
    settings/
      mcp.json
    hooks/
      validate-report.*
      run-analysis-tests.*
  apps/
    web/
  packages/
    analysis-engine/
    kiro-mcp-server/
  demo-data/
  artifacts/
  README.md
  LICENSE
```

## Video Production Notes

Use the **Winning Demo Path** above as the actual video structure. Keep the recording under three minutes and prioritize working product footage over explanation.

The video should avoid:

- long setup steps
- raw terminal debugging
- copyrighted music
- third-party trademarks beyond necessary development tools
- unsupported claims about clinical usefulness

The video should include:

- the app running on its intended platform
- the `.kiro/` directory at repo root
- at least one visible Kiro spec or steering document
- at least one visible hook or MCP-backed workflow
- the final robust / fragile / suspicious verdict
- the exported reproducibility report

## Judging Alignment

### Implementation

Strong because the app includes a real computational engine, deterministic analysis tools, Kiro MCP integration, hooks, specs, and reproducible artifacts.

Minimum bar: the repo must be installable and the demo path must run consistently.

### Innovation and Design

Strong if the UI makes claim auditing easy to understand through a clear verdict, stability charts, warnings, heatmaps, and report exports.

Design priority: make the "claim audit" story more prominent than the raw bioinformatics methods.

### Social Good

Strong if framed around reproducibility and access: helping researchers avoid fragile claims and giving smaller teams practical bioinformatics quality controls.

Pitch priority: explain how fragile claims waste research time, money, and follow-up experiments.

## Out of Scope for V1

- Broad "AI agent for all bioinformatics"
- SNP interpretation
- Full multi-omics contradiction detection
- Literature validation
- Paper-to-pipeline automation
- Real clinical interpretation
- Claims that a candidate biomarker is clinically proven
- General-purpose normalization assistant

## Key Product Boundaries

- Do not claim clinical validation.
- Do not diagnose patients.
- Do not imply real biomarkers are proven from demo data.
- Prefer demo/synthetic datasets unless third-party data licensing is clear.
- Keep the analysis reproducible and inspectable.
- Make the Kiro usage visible in the repository and demo.
- Keep the demo understandable to non-bio judges.

## Next Build Decisions

- Choose stack: likely Python analysis engine plus a web UI.
- Decide whether to use a fully synthetic dataset or an open licensed public dataset.
- Choose first clustering method for MVP.
- Choose first stability metric for MVP.
- Choose the first claim verdict thresholds.
- Decide deployment target or local-only submission path.
- Decide exact one-command setup flow for judges.
