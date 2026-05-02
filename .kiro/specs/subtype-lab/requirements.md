# Requirements Document

## Introduction

SubtypeLab is a bioinformatics claim-auditing tool for cancer subtyping and biomarker discovery. Given a gene-expression-style dataset and a biological claim — such as "these samples form three subtypes" or "these genes distinguish subtype A from subtype B" — the system attempts to break the claim through deterministic stress tests.

The core value is reproducibility assurance: SubtypeLab checks whether a subtype or biomarker result survives noisy samples, missing features, cohort splits, normalization variants, and batch-like shifts. It is positioned as a research-support tool for hypothesis generation, not as a diagnostic or clinical decision-making system.

The MVP targets students, small labs, and under-resourced research teams who need practical bioinformatics quality controls before trusting or presenting a result.

### Technology Stack

- **Analysis_Engine**: Python with FastAPI. Scientific computation uses NumPy, SciPy, scikit-learn, and pandas. The engine runs as a local HTTP service.
- **Web_UI**: React with Vite and TypeScript. Visualization uses Plotly.js or Recharts. The UI is served locally and communicates with the Analysis_Engine over localhost.
- **MCP_Server**: Python, implemented as a separate entry point that wraps Analysis_Engine functions and exposes them via the Model Context Protocol.
- **Demo Data**: A fully synthetic gene-expression-style dataset generated at build/startup time. No external datasets or cloud services are required.
- **Deployment Target**: Local-first. The entire system runs on a developer or researcher's machine. A single command (`docker compose up` or equivalent) starts all services. No cloud dependency is required for the core demo.

### Async Audit Execution

Claim audits run as asynchronous background jobs on the Analysis_Engine. The Web_UI polls a job-status endpoint to display progress. The following rules apply:

- WHEN an audit job is started, THE Analysis_Engine SHALL return a job ID immediately without blocking.
- WHILE an audit job is running, THE Analysis_Engine SHALL expose a status endpoint returning the current phase, completed perturbation count, total perturbation count, and elapsed time.
- WHEN an audit job completes successfully, THE Analysis_Engine SHALL transition the job to a `completed` state and make all results available via the job ID.
- WHEN an audit job fails, THE Analysis_Engine SHALL transition the job to a `failed` state, record the error message and the phase at which failure occurred, and preserve any partial artifacts already written to disk.
- V1 SHALL NOT support step-level resume. A failed audit must be restarted from the beginning.
- FOR ALL job IDs, the status endpoint SHALL remain queryable for at least one hour after job completion or failure.

---

## Glossary

- **Analysis_Engine**: The Python backend module responsible for all deterministic computation including clustering, perturbation, stability scoring, and biomarker ranking.
- **Audit**: The process of stress-testing a biological claim by running perturbation suites and computing a verdict from resulting metrics.
- **Batch_Effect**: Systematic technical variation in expression data introduced by differences in sample processing, sequencing run, or laboratory conditions.
- **Biomarker**: A measurable feature (e.g., gene expression level) used to distinguish biological states or subtypes.
- **Claim**: A user-provided or auto-generated biological assertion about the dataset, such as "these samples form N subtypes" or "these genes distinguish subtype A from subtype B."
- **Claim_Verdict**: A computed classification of a claim as `robust`, `fragile`, or `suspicious`, derived from stability metrics and perturbation results.
- **Cluster_Consistency_Score**: A numeric score in [0, 1] measuring how consistently samples are assigned to the same cluster across perturbation runs.
- **Dataset**: A CSV or TSV file containing a feature matrix (rows = samples, columns = features/genes) plus an optional metadata file with sample annotations.
- **Dataset_Hash**: A deterministic SHA-256 hash of the input dataset file used to uniquely identify the data version in reproducibility reports.
- **MCP_Server**: The local Model Context Protocol server that exposes Analysis_Engine tools to Kiro and the Web_UI.
- **Normalization_Variant**: One of the supported normalization strategies applied to the Dataset before analysis (e.g., log2, z-score, quantile, none).
- **Perturbation**: A controlled modification of the Dataset or analysis parameters designed to test claim stability (e.g., dropping features, adding noise, splitting cohorts).
- **Reproducibility_Report**: A structured artifact containing the Dataset_Hash, method parameters, stability metrics, plots, and Claim_Verdict for a completed Audit.
- **Stability_Score**: An aggregate numeric score in [0, 1] summarizing subtype assignment stability across all perturbation runs.
- **Subtype**: A biologically meaningful group of samples identified by clustering or provided as metadata labels.
- **Web_UI**: The browser-based front end through which users load data, submit claims, trigger analyses, and view results.

---

## Requirements

### Requirement 1: Dataset Loading

**User Story:** As a researcher, I want to load a gene-expression-style dataset into SubtypeLab, so that I can audit biological claims against my own data or a provided demo dataset.

#### Acceptance Criteria

1. THE Web_UI SHALL provide an option to load a built-in demo dataset without requiring a file upload.
2. WHEN a user uploads a CSV or TSV file, THE Analysis_Engine SHALL parse the file into an in-memory feature matrix with samples as rows and features as columns.
3. WHEN a user uploads a metadata file, THE Analysis_Engine SHALL associate sample annotations with the corresponding rows in the feature matrix.
4. IF a uploaded file is not valid CSV or TSV format, THEN THE Web_UI SHALL display a descriptive error message identifying the format violation.
5. IF the feature matrix contains fewer than 10 samples or fewer than 5 features, THEN THE Analysis_Engine SHALL return a validation error stating the minimum size requirements.
6. WHEN a dataset is successfully loaded, THE Analysis_Engine SHALL compute and return a Dataset_Hash for the loaded file.
7. FOR ALL valid Dataset files, parsing then re-serializing then parsing SHALL produce a feature matrix with identical dimensions and values (round-trip property).

---

### Requirement 2: Dataset Quality Metrics

**User Story:** As a researcher, I want to see basic quality metrics for my loaded dataset, so that I can understand its characteristics before running an audit.

#### Acceptance Criteria

1. WHEN a dataset is successfully loaded, THE Analysis_Engine SHALL compute and return the sample count, feature count, missing value count, and missing value percentage.
2. WHEN a dataset is successfully loaded, THE Analysis_Engine SHALL compute and return per-feature summary statistics including mean, standard deviation, and zero-value percentage.
3. IF the missing value percentage exceeds 20%, THEN THE Web_UI SHALL display a warning flag indicating high missingness.
4. IF any feature has a zero-value percentage exceeding 80%, THEN THE Web_UI SHALL display a warning flag identifying that feature as a low-variance candidate.
5. WHEN quality metrics are computed, THE Web_UI SHALL display the metrics in a summary panel before the user proceeds to claim entry.

---

### Requirement 3: Claim Entry

**User Story:** As a researcher, I want to provide or select a biological claim about my dataset, so that SubtypeLab knows what assertion to audit.

#### Acceptance Criteria

1. THE Web_UI SHALL present at least three auto-generated claim templates: "These samples form N subtypes," "These genes distinguish subtype A from subtype B," and "These biomarkers are stable across cohorts."
2. WHEN a user selects an auto-generated claim template, THE Web_UI SHALL populate the claim input field with the selected template text.
3. THE Web_UI SHALL allow the user to edit the claim text freely before submitting it for audit.
4. WHEN a user submits a claim, THE Analysis_Engine SHALL parse the claim and extract the claim type (subtype-count, biomarker-discrimination, or cohort-stability) and any numeric parameters (e.g., N subtype count).
5. IF a submitted claim contains language from the prohibited clinical terms list (e.g., "diagnostic," "clinically proven," "clinical validation"), THEN THE Web_UI SHALL reject the claim and display a message stating that clinical interpretation language is not supported.
6. IF a submitted claim cannot be parsed into a recognized claim type, THEN THE Analysis_Engine SHALL return a descriptive error identifying the unrecognized pattern.

---

### Requirement 4: Baseline Analysis

**User Story:** As a researcher, I want to run a baseline subtype or biomarker analysis on my dataset, so that I have a reference result before stress-testing the claim.

#### Acceptance Criteria

1. WHEN a user triggers baseline analysis, THE Analysis_Engine SHALL apply the selected Normalization_Variant to the feature matrix before clustering.
2. WHEN a user triggers baseline analysis with a subtype-count claim, THE Analysis_Engine SHALL run k-means clustering with k equal to the claimed subtype count and return cluster assignments for all samples.
3. WHEN a user triggers baseline analysis with a biomarker-discrimination claim, THE Analysis_Engine SHALL compute a differential expression score for each feature between the specified subtypes and return a ranked feature list.
4. WHEN baseline analysis completes, THE Analysis_Engine SHALL return the cluster assignments, a within-cluster sum of squares value, and a silhouette score for the clustering result.
5. WHEN baseline analysis completes, THE Web_UI SHALL display a heatmap or PCA projection of the clustered samples.
6. IF baseline analysis fails due to a numerical error, THEN THE Analysis_Engine SHALL return a structured error message identifying the computation step that failed.
7. THE Analysis_Engine SHALL support at least four Normalization_Variants: log2, z-score, quantile, and none.

---

### Requirement 5: Claim Audit — Perturbation Suite

**User Story:** As a researcher, I want SubtypeLab to stress-test my claim across multiple perturbations, so that I can see whether the result is robust or fragile.

#### Acceptance Criteria

1. WHEN a user triggers a claim audit, THE Analysis_Engine SHALL run the full perturbation suite consisting of at least five perturbation types: missing-feature dropout, noisy-sample injection, cohort split, normalization variant swap, and batch-like shift.
2. WHEN running missing-feature dropout perturbations, THE Analysis_Engine SHALL drop a random 10%, 20%, and 30% of features and rerun clustering for each dropout level.
3. WHEN running noisy-sample perturbations, THE Analysis_Engine SHALL add Gaussian noise at standard deviations of 0.1, 0.5, and 1.0 relative to the feature scale and rerun clustering for each noise level.
4. WHEN running cohort-split perturbations, THE Analysis_Engine SHALL partition samples into two equal halves using at least three different random seeds and rerun clustering on each half.
5. WHEN running normalization-variant perturbations, THE Analysis_Engine SHALL rerun clustering under each supported Normalization_Variant and compare cluster assignments to the baseline.
6. WHEN running batch-like shift perturbations, THE Analysis_Engine SHALL apply a synthetic mean shift to a randomly selected 30% of samples and rerun clustering.
7. WHEN all perturbation runs complete, THE Analysis_Engine SHALL compute a Cluster_Consistency_Score for each perturbation type by comparing perturbed cluster assignments to the baseline using the Adjusted Rand Index.
8. WHEN all perturbation runs complete, THE Analysis_Engine SHALL compute an aggregate Stability_Score as the mean Cluster_Consistency_Score across all perturbation runs.
9. FOR ALL perturbation runs on the same Dataset with the same random seed, THE Analysis_Engine SHALL produce identical cluster assignments (determinism property).

---

### Requirement 6: Claim Verdict

**User Story:** As a researcher, I want to receive a clear verdict on my claim, so that I know whether to trust, investigate further, or discard the result.

#### Acceptance Criteria

1. WHEN the perturbation suite completes, THE Analysis_Engine SHALL compute a Claim_Verdict from the Stability_Score using the following thresholds: Stability_Score ≥ 0.75 → `robust`; 0.50 ≤ Stability_Score < 0.75 → `suspicious`; Stability_Score < 0.50 → `fragile`.
2. WHEN a Claim_Verdict is computed, THE Web_UI SHALL display the verdict prominently with a color indicator: green for `robust`, yellow for `suspicious`, and red for `fragile`.
3. WHEN a Claim_Verdict is computed, THE Web_UI SHALL display the Stability_Score and the per-perturbation Cluster_Consistency_Scores alongside the verdict.
4. WHEN a Claim_Verdict is `fragile` or `suspicious`, THE Web_UI SHALL display at least one specific warning flag identifying the perturbation type that produced the lowest Cluster_Consistency_Score.
5. THE Analysis_Engine SHALL derive the Claim_Verdict exclusively from computed metrics and SHALL NOT use freeform model-generated text as a basis for the verdict.

---

### Requirement 7: Biomarker Robustness Ranking

**User Story:** As a researcher, I want to see which candidate biomarkers survive perturbations, so that I can distinguish stable signals from one-run artifacts.

#### Acceptance Criteria

1. WHEN a claim audit completes for a biomarker-discrimination or subtype-count claim, THE Analysis_Engine SHALL compute a robustness score for each feature by measuring how consistently the feature ranks in the top-K discriminating features across perturbation runs, where K equals 10% of total features or 20 features, whichever is smaller.
2. WHEN biomarker robustness scores are computed, THE Analysis_Engine SHALL return a ranked list of features sorted by descending robustness score.
3. WHEN biomarker robustness scores are computed, THE Web_UI SHALL display the top 20 features in a ranked table showing feature name, robustness score, and baseline differential expression score.
4. IF a feature appears in the top-K list in fewer than 50% of perturbation runs, THEN THE Analysis_Engine SHALL flag that feature as a one-run artifact in the ranked list.
5. FOR ALL valid datasets with at least two subtypes, the set of features ranked in the top-K by robustness score SHALL be a subset of features that appear in the top-K in at least one perturbation run (subset property).

---

### Requirement 8: Visualization

**User Story:** As a researcher, I want to see visual representations of the clustering and stability results, so that I can interpret the audit findings quickly.

#### Acceptance Criteria

1. WHEN baseline analysis completes, THE Web_UI SHALL render a heatmap of the top 50 most variable features across all samples, with samples grouped by cluster assignment.
2. WHEN baseline analysis completes, THE Web_UI SHALL render a 2D PCA projection of samples colored by cluster assignment.
3. WHEN the claim audit completes, THE Web_UI SHALL render a cluster consistency chart showing the Cluster_Consistency_Score for each perturbation type as a bar chart.
4. WHEN the claim audit completes and the Stability_Score is below 0.75, THE Web_UI SHALL highlight the perturbation bars with Cluster_Consistency_Score below 0.50 in red.
5. THE Web_UI SHALL render all visualizations within 5 seconds of receiving the analysis results from the Analysis_Engine.
6. IF the Analysis_Engine returns no cluster assignments, THEN THE Web_UI SHALL display a placeholder message instead of an empty chart.

---

### Requirement 9: Reproducibility Report

**User Story:** As a researcher, I want to export a reproducibility report for my audit, so that I can share, archive, or review the evidence behind the claim verdict.

#### Acceptance Criteria

1. WHEN a claim audit completes, THE Web_UI SHALL make a report export action available to the user.
2. WHEN a user triggers report export, THE Analysis_Engine SHALL generate a Reproducibility_Report containing: Dataset_Hash, claim text, Normalization_Variant used, perturbation parameters, Stability_Score, per-perturbation Cluster_Consistency_Scores, Claim_Verdict, and links to all generated plot artifacts.
3. WHEN a Reproducibility_Report is generated, THE Analysis_Engine SHALL embed a disclaimer stating that outputs are for research support only and are not suitable for clinical or diagnostic use.
4. IF a Reproducibility_Report is missing any of the required fields (Dataset_Hash, Claim_Verdict, Stability_Score, perturbation parameters), THEN THE Analysis_Engine SHALL return a validation error and SHALL NOT produce the report file.
5. WHEN a Reproducibility_Report is exported, THE Analysis_Engine SHALL write the report to a deterministic file path derived from the Dataset_Hash and a timestamp.
6. FOR ALL completed audits, generating a report immediately after the audit and generating a report one minute later SHALL produce reports with identical Dataset_Hash, Claim_Verdict, and Stability_Score values (idempotence property).

---

### Requirement 10: MCP Server Tools

**User Story:** As a developer integrating with Kiro, I want the Analysis_Engine to be accessible through a local MCP server, so that Kiro can invoke deterministic bioinformatics tools directly.

#### Acceptance Criteria

1. THE MCP_Server SHALL expose the following tools: `inspect_dataset`, `run_normalization`, `run_subtyping`, `run_perturbation_suite`, `rank_robust_biomarkers`, `audit_biological_claim`, and `generate_reproducibility_report`.
2. WHEN `inspect_dataset` is called with a valid file path, THE MCP_Server SHALL return the sample count, feature count, missing value count, and Dataset_Hash.
3. WHEN `run_subtyping` is called with a feature matrix and a subtype count, THE MCP_Server SHALL return cluster assignments and a silhouette score.
4. WHEN `run_perturbation_suite` is called with a feature matrix and perturbation configuration, THE MCP_Server SHALL return per-perturbation Cluster_Consistency_Scores and an aggregate Stability_Score.
5. WHEN `audit_biological_claim` is called with a claim string and analysis results, THE MCP_Server SHALL return a Claim_Verdict derived from computed metrics.
6. WHEN `generate_reproducibility_report` is called with complete audit results, THE MCP_Server SHALL return a structured report object and write the report artifact to disk.
7. IF any MCP_Server tool is called with missing required parameters, THEN THE MCP_Server SHALL return a structured error response identifying the missing parameters.
8. FOR ALL MCP_Server tool calls with identical inputs and random seeds, THE MCP_Server SHALL return identical outputs (determinism property).

---

### Requirement 11: Clinical Language Guardrails

**User Story:** As a tool maintainer, I want SubtypeLab to block unsupported clinical language in claims and reports, so that the tool is not misused for clinical interpretation.

#### Acceptance Criteria

1. THE Analysis_Engine SHALL maintain a prohibited terms list containing at minimum: "diagnostic," "clinically proven," "clinical validation," "FDA approved," "patient diagnosis," and "treatment recommendation."
2. WHEN a claim is submitted containing any term from the prohibited terms list, THE Web_UI SHALL reject the claim before analysis begins and display a message explaining that clinical interpretation language is not supported.
3. WHEN a Reproducibility_Report is generated, THE Analysis_Engine SHALL scan the report text for prohibited terms and SHALL return a validation error if any are found.
4. WHEN a Kiro hook validates a report artifact, THE hook SHALL fail the validation check if the report file contains any term from the prohibited terms list.
5. THE prohibited terms list SHALL be stored in a configuration file that can be updated without modifying Analysis_Engine source code.

---

### Requirement 13: Demo Data Generation

**User Story:** As a researcher evaluating SubtypeLab, I want a built-in synthetic dataset to be available immediately, so that I can run the full demo workflow without uploading my own data or depending on external sources.

#### Acceptance Criteria

1. THE Analysis_Engine SHALL include a demo data generator that produces a synthetic gene-expression-style feature matrix with at least 80 samples and at least 200 features.
2. THE demo dataset SHALL contain at least three embedded cluster signals with known ground-truth subtype labels, such that a baseline k-means run with k=3 produces a silhouette score above 0.4.
3. THE demo dataset SHALL be generated deterministically from a fixed random seed so that the same dataset is produced on every run.
4. WHEN the system starts, THE Analysis_Engine SHALL make the demo dataset available via the `inspect_dataset` MCP tool and the dataset-loading endpoint without requiring any file upload.
5. THE demo dataset SHALL be accompanied by a synthetic metadata file assigning each sample a subtype label and a batch label.
6. THE demo dataset SHALL NOT reference or depend on any real patient data, licensed datasets, or external network resources.
7. FOR ALL runs with the same fixed seed, the generated demo dataset SHALL have identical dimensions, values, and ground-truth labels (determinism property).

---

### Requirement 14: Local One-Command Setup

**User Story:** As a judge or collaborator, I want to start the entire SubtypeLab system with a single command, so that I can evaluate the demo without manual configuration steps.

#### Acceptance Criteria

1. THE repository SHALL include a `docker-compose.yml` (or equivalent) that starts the Analysis_Engine, the MCP_Server, and the Web_UI with a single `docker compose up` command.
2. WHEN the one-command setup completes, THE Web_UI SHALL be accessible at `http://localhost:3000` (or a documented equivalent port) without additional configuration.
3. WHEN the one-command setup completes, THE Analysis_Engine SHALL be accessible at `http://localhost:8000` (or a documented equivalent port).
4. THE setup SHALL NOT require any external API keys, cloud credentials, or network access beyond pulling public base images.
5. THE repository SHALL include a `README.md` with a "Quick Start" section containing the exact one-command invocation and the expected URLs.
6. IF the one-command setup fails due to a port conflict, THE documentation SHALL describe how to override the default ports via environment variables.

---

### Requirement 15: Audit Job Lifecycle

**User Story:** As a researcher, I want to see real-time progress while my claim audit is running, so that I know the system is working and can estimate when results will be ready.

#### Acceptance Criteria

1. WHEN a user triggers a claim audit, THE Analysis_Engine SHALL start the audit as a background job and return a job ID to the Web_UI immediately, without blocking the HTTP response.
2. WHEN a job is running, THE Analysis_Engine SHALL expose a `/jobs/{job_id}/status` endpoint returning: job state (`queued`, `running`, `completed`, `failed`), current phase name, completed perturbation count, total perturbation count, and elapsed seconds.
3. WHILE a job is running, THE Web_UI SHALL poll the status endpoint at least once every two seconds and display a progress indicator showing the current phase and percentage complete.
4. WHEN a job transitions to `completed`, THE Web_UI SHALL automatically fetch and display the full audit results without requiring a manual page refresh.
5. WHEN a job transitions to `failed`, THE Analysis_Engine SHALL record the error message and the phase name at which the failure occurred, and THE Web_UI SHALL display the error message and phase to the user.
6. WHEN a job fails, THE Analysis_Engine SHALL preserve any partial artifacts (plots, intermediate scores) already written to disk for that job, accessible via a `/jobs/{job_id}/artifacts` endpoint.
7. V1 SHALL NOT support resuming a failed job from the point of failure; the user must restart the audit.
8. THE Analysis_Engine SHALL retain job state and artifacts for at least one hour after the job reaches a terminal state (`completed` or `failed`).
9. FOR ALL job IDs, the status endpoint SHALL return a consistent state throughout the retention window (idempotence property).

---

### Requirement 12: Kiro Workflow Hooks

**User Story:** As a developer, I want Kiro hooks to enforce workflow quality automatically, so that analysis engine changes are tested and report artifacts are validated before use.

#### Acceptance Criteria

1. WHEN any Analysis_Engine source file is modified, THE test_hook SHALL automatically run the Analysis_Engine test suite and report pass or fail status.
2. WHEN a Reproducibility_Report artifact is written to disk, THE report_validation_hook SHALL verify that the report contains Dataset_Hash, Claim_Verdict, Stability_Score, and perturbation parameters, and SHALL fail if any field is absent.
3. WHEN a report artifact is validated by the report_validation_hook, THE hook SHALL check for prohibited clinical terms and SHALL fail if any are found.
4. WHEN the test_hook detects a test failure, THE hook SHALL block the workflow step that triggered the hook and display the failing test output.
5. THE hooks SHALL be defined as configuration files in the `.kiro/hooks/` directory and SHALL NOT require manual invocation by the developer.

