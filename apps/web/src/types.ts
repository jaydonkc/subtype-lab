export type QualityMetrics = {
  sample_count: number;
  feature_count: number;
  missing_value_count: number;
  missing_value_percentage: number;
  feature_summaries: Array<{
    feature: string;
    mean: number;
    std: number;
    zero_value_percentage: number;
  }>;
  warnings: string[];
};

export type DatasetDescription = {
  dataset_id: string;
  dataset_hash: string;
  quality: QualityMetrics;
  preview: {
    index: string[];
    columns: string[];
    values: number[][];
  };
  metadata?: {
    index: string[];
    columns: string[];
    values: Array<Array<string | number | null>>;
  } | null;
  source?: {
    name: string;
    url: string;
    doi?: string;
    license?: string;
    loaded_from?: string;
    notes?: string;
  } | null;
};

export type BaselineResult = {
  dataset_id: string;
  dataset_hash: string;
  claim_text: string;
  claim_type: string;
  subtype_count: number;
  normalization_variant: string;
  cluster_labels: number[];
  wcss: number;
  silhouette_score: number;
  pca: Array<{ sample_id: string; pc1: number; pc2: number; cluster: number }>;
  heatmap: {
    samples: string[];
    features: string[];
    values: number[][];
    clusters: number[];
  };
  top_biomarkers: BiomarkerRank[];
};

export type BiomarkerRank = {
  feature: string;
  robustness_score: number;
  baseline_score: number;
  one_run_artifact: boolean;
};

export type JobStatus = {
  job_id: string;
  state: "queued" | "running" | "completed" | "failed";
  phase: string;
  completed: number;
  total: number;
  elapsed_seconds: number;
  error: string | null;
};

export type AuditResult = BaselineResult & {
  stability_score: number;
  per_type_scores: Record<string, number>;
  verdict: "robust" | "suspicious" | "fragile";
  warnings: string[];
  biomarkers: BiomarkerRank[];
  report: {
    report_id?: string;
    paths?: {
      json?: string;
      html?: string;
    };
  };
};

export type ReproducibilityReport = {
  report_id: string;
  generated_at: string;
  disclaimer: string;
  dataset_hash: string;
  claim_text: string;
  normalization_variant: string;
  stability_score: number;
  claim_verdict: string;
  warnings: string[];
  top_biomarkers: BiomarkerRank[];
};

export type KiroVerdictExplanation = {
  mode: "kiro_guided_explanation";
  verdict_source: "computed_metrics";
  kiro_role: string;
  headline: string;
  summary: string;
  threshold_used: string;
  evidence: Array<{
    label: string;
    value: string;
    interpretation: string;
  }>;
  reasoning_steps: string[];
  guardrails: string[];
  warnings: string[];
  next_steps: string[];
};

export type AgentFinding = {
  title: string;
  finding_type: "claim" | "marker" | "research_gap" | "risk";
  confidence: "high" | "medium" | "low";
  evidence: string;
  interpretation: string;
  recommended_next_step: string;
};

export type AgentFindings = {
  mode: "deterministic_agent" | "agentic_ai";
  provider: string;
  model: string;
  headline: string;
  executive_summary: string;
  findings: AgentFinding[];
  agent_trace: string[];
  guardrails: string[];
  warnings: string[];
  evidence_snapshot: {
    marker_evidence: Array<{
      feature: string;
      robustness_score: number;
      baseline_score: number;
      one_run_artifact: boolean;
      research_gap_score: number;
      literature: {
        status: string;
        evidence_level: string;
        total_hits: number;
        summary: string;
        top_titles: string[];
      };
    }>;
  };
};

export type LiteratureEvidence = {
  marker: string;
  context: string;
  query: string;
  source: string;
  status: "ok" | "unavailable" | "demo_only";
  evidence_level: "known" | "emerging" | "sparse" | "underexplored" | "unavailable" | "demo_synthetic";
  total_hits: number;
  works_examined: number;
  summary: string;
  caveats: string[];
  hits: Array<{
    title: string;
    journal: string;
    year: string;
    authors: string[];
    url: string;
    source: string;
  }>;
};
