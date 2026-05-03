import type {
  AgentFindings,
  AuditResult,
  BaselineResult,
  DatasetDescription,
  JobStatus,
  KiroVerdictExplanation,
  LiteratureEvidence,
  ReproducibilityReport,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatDetail(body.detail ?? response.statusText));
  }

  return response.json() as Promise<T>;
}

export function loadDemoDataset(): Promise<DatasetDescription> {
  return request<DatasetDescription>("/api/datasets/demo");
}

export function loadWdbcDataset(): Promise<DatasetDescription> {
  return request<DatasetDescription>("/api/datasets/wdbc");
}

export async function uploadDataset(file: File, metadataFile?: File | null): Promise<DatasetDescription> {
  const body = new FormData();
  body.append("file", file);
  if (metadataFile) {
    body.append("metadata_file", metadataFile);
  }
  const response = await fetch(`${API_BASE}/api/datasets/upload`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatDetail(payload.detail ?? response.statusText));
  }
  return response.json() as Promise<DatasetDescription>;
}

export function runBaseline(
  datasetId: string,
  claimText: string,
  normalizationVariant: string,
): Promise<BaselineResult> {
  return request<BaselineResult>("/api/baseline", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: datasetId,
      claim_text: claimText,
      normalization_variant: normalizationVariant,
    }),
  });
}

export function startAudit(
  datasetId: string,
  claimText: string,
  normalizationVariant: string,
): Promise<{ job_id: string; state: string }> {
  return request("/api/jobs/audit", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: datasetId,
      claim_text: claimText,
      normalization_variant: normalizationVariant,
    }),
  });
}

export function getJobStatus(jobId: string): Promise<JobStatus> {
  return request<JobStatus>(`/api/jobs/${jobId}/status`);
}

export async function getAuditResult(jobId: string): Promise<AuditResult> {
  const payload = await request<{ result: AuditResult }>(`/api/jobs/${jobId}/artifacts`);
  return payload.result;
}

export function getKiroExplanation(jobId: string): Promise<KiroVerdictExplanation> {
  return request<KiroVerdictExplanation>(`/api/jobs/${jobId}/kiro-explanation`);
}

export function getAgentFindings(jobId: string): Promise<AgentFindings> {
  return request<AgentFindings>(`/api/jobs/${jobId}/agent-findings`);
}

export function getReport(reportId: string): Promise<ReproducibilityReport> {
  return request<ReproducibilityReport>(`/api/reports/${reportId}`);
}

export function getLiteratureEvidence(
  marker: string,
  context: string,
  limit = 5,
): Promise<LiteratureEvidence> {
  return request<LiteratureEvidence>("/api/literature/evidence", {
    method: "POST",
    body: JSON.stringify({
      marker,
      context,
      limit,
    }),
  });
}

export async function getReportHtml(reportId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/reports/${reportId}/html`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatDetail(payload.detail ?? response.statusText));
  }
  return response.text();
}

function formatDetail(detail: unknown): string {
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}
