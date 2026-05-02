export type QualityMetrics = {
  sample_count: number;
  feature_count: number;
  missing_value_count: number;
  missing_value_percentage: number;
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
    paths?: {
      json?: string;
      html?: string;
    };
  };
};
