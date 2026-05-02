# Implementation Tasks

## Product Contract

Build SubtypeLab as a deterministic bioinformatics reproducibility workbench, not as a chat wrapper. Kiro is part of the product story through specs, steering, hooks, and MCP, but all scientific verdicts must come from executable analysis code.

## Completed Core

- [x] Create monorepo-style scaffold with `apps/web`, `packages/analysis-engine`, `packages/kiro-mcp-server`, `artifacts`, and `demo-data`.
- [x] Keep `.kiro/` at repo root and ensure it is not ignored.
- [x] Add Kiro requirements, design, tasks, steering docs, hooks, and MCP settings.
- [x] Add MIT license and public-repo-ready README.
- [x] Add Docker Compose for one-command local startup.
- [x] Generate deterministic synthetic expression-style demo data.
- [x] Write synthetic expression and metadata CSV files at backend startup.
- [x] Implement CSV/TSV expression matrix parsing.
- [x] Implement optional CSV/TSV metadata parsing and sample alignment.
- [x] Compute dataset hash from uploaded bytes.
- [x] Compute quality metrics, per-feature summaries, and warning flags.
- [x] Implement claim parsing for subtype, biomarker, and cohort-stability language.
- [x] Block prohibited clinical-language claims using a config file.
- [x] Implement normalization variants: `none`, `log2`, `z-score`, `zscore`, and `quantile`.
- [x] Implement deterministic k-means, WCSS, silhouette score, and PCA projection.
- [x] Implement adjusted Rand index without relying on model-generated text.
- [x] Implement 17-run perturbation suite covering dropout, noise, cohort split, normalization swap, and batch-like shift.
- [x] Compute stability score and verdict thresholds.
- [x] Rank robust biomarkers and flag one-run artifacts.
- [x] Generate JSON and HTML reproducibility reports.
- [x] Validate reports for required fields and prohibited language.
- [x] Add report retrieval endpoints for JSON and HTML.
- [x] Add background audit job lifecycle with polling status.
- [x] Add API aliases matching the original Kiro spec paths.
- [x] Implement Kiro MCP tools that call deterministic analysis functions.
- [x] Allow MCP `inspect_dataset` to inspect the demo dataset or a local file path.

## Completed UI

- [x] Build a focused single-page lab workflow instead of a marketing landing page.
- [x] Add demo dataset loading.
- [x] Add expression matrix upload.
- [x] Add optional metadata upload.
- [x] Display sample count, feature count, missingness, dataset hash, metadata presence, warnings, and feature summaries.
- [x] Render dataset preview heatmap.
- [x] Add editable claim templates.
- [x] Add normalization selector.
- [x] Run baseline analysis from the selected dataset.
- [x] Render PCA projection.
- [x] Render top-variable feature heatmap grouped by baseline clusters.
- [x] Render baseline and audit biomarker tables.
- [x] Run asynchronous claim audit and poll progress.
- [x] Render verdict, stability score, perturbation score bars, warnings, and report paths.
- [x] Add JSON report download.
- [x] Add HTML report download.

## Completed Verification Targets

- [x] Backend tests cover demo data, metadata alignment, claim guardrails, baseline output, perturbation determinism, audit reports, API aliases, and report retrieval.
- [x] Frontend has a production build script.
- [x] Report validation script checks report artifacts.
- [x] Docker setup builds backend and frontend containers.
- [x] README documents local, Docker, troubleshooting, and demo workflow.
- [x] `KIRO_USAGE.md` explains vibe coding, specs, steering, hooks, MCP, and Kiro-native workflow.

## Final Submission Checks

- [ ] Run backend test suite from the current tree.
- [ ] Run frontend production build from the current tree.
- [ ] Run frontend dependency audit.
- [ ] Generate at least one report and run report validation.
- [ ] Smoke-test MCP tool calls from the current tree.
- [ ] Rebuild and verify Docker Compose after final edits.
- [ ] Manually click through the browser demo:
  - load demo dataset
  - inspect quality panel
  - run baseline
  - run audit
  - download JSON report
  - download HTML report
  - show `.kiro/` contents
- [ ] Create public GitHub repository.
- [ ] Commit `.kiro/` and all source files.
- [ ] Confirm GitHub detects the MIT license.
- [ ] Record public demo video under three minutes.

## Stretch After Submission

- [ ] Add persistent job storage.
- [ ] Add real public dataset import templates with explicit licensing notes.
- [ ] Add metadata-aware batch diagnostics.
- [ ] Add user-selectable perturbation budgets.
- [ ] Add a richer browser report viewer.
- [ ] Package Kiro steering, hooks, MCP settings, and spec template as a reusable Kiro Power.

## Notes

The current implementation chooses deterministic NumPy/Pandas code over heavier scientific and charting libraries. That keeps the judge path simple and makes the key claim easier to defend: every verdict is reproducible and computed by the app, not produced by a language model.
