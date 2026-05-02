import type { AuditResult, BaselineResult, DatasetDescription, JobStatus } from "./types";

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
    throw new Error(body.detail ?? response.statusText);
  }

  return response.json() as Promise<T>;
}

export function loadDemoDataset(): Promise<DatasetDescription> {
  return request<DatasetDescription>("/api/datasets/demo");
}

export function runBaseline(claimText: string, normalizationVariant: string): Promise<BaselineResult> {
  return request<BaselineResult>("/api/baseline", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: "demo",
      claim_text: claimText,
      normalization_variant: normalizationVariant,
    }),
  });
}

export function startAudit(claimText: string, normalizationVariant: string): Promise<{ job_id: string; state: string }> {
  return request("/api/jobs/audit", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: "demo",
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
