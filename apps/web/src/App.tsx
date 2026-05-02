import { useEffect, useMemo, useState } from "react";
import {
  getAuditResult,
  getJobStatus,
  loadDemoDataset,
  runBaseline,
  startAudit,
} from "./api";
import type { AuditResult, BaselineResult, DatasetDescription, JobStatus } from "./types";

const CLAIMS = [
  "These samples form three stable subtypes.",
  "These genes distinguish subtype A from subtype B.",
  "These biomarkers are stable across cohorts.",
];

const NORMALIZATIONS = ["z-score", "log2", "quantile", "none"];

export function App() {
  const [dataset, setDataset] = useState<DatasetDescription | null>(null);
  const [claim, setClaim] = useState(CLAIMS[0]);
  const [normalization, setNormalization] = useState("z-score");
  const [baseline, setBaseline] = useState<BaselineResult | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void handleLoadDemo();
  }, []);

  useEffect(() => {
    if (!status?.job_id || status.state === "completed" || status.state === "failed") {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const next = await getJobStatus(status.job_id);
        setStatus(next);
        if (next.state === "completed") {
          const result = await getAuditResult(next.job_id);
          setAudit(result);
        }
      } catch (err) {
        setError(errorMessage(err));
      }
    }, 1200);

    return () => window.clearInterval(timer);
  }, [status?.job_id, status?.state]);

  const progress = useMemo(() => {
    if (!status) return 0;
    return Math.min(100, Math.round((status.completed / Math.max(1, status.total)) * 100));
  }, [status]);

  async function handleLoadDemo() {
    setError(null);
    setLoading(true);
    try {
      setDataset(await loadDemoDataset());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleBaseline() {
    setError(null);
    setAudit(null);
    setStatus(null);
    setLoading(true);
    try {
      setBaseline(await runBaseline(claim, normalization));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAudit() {
    setError(null);
    setAudit(null);
    setLoading(true);
    try {
      const job = await startAudit(claim, normalization);
      setStatus({
        job_id: job.job_id,
        state: "queued",
        phase: "queued",
        completed: 0,
        total: 17,
        elapsed_seconds: 0,
        error: null,
      });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="masthead">
        <div>
          <p className="eyebrow">Kiro-powered reproducibility QA</p>
          <h1>SubtypeLab</h1>
          <p>
            A crash-test lab for cancer subtype and biomarker claims. The app runs deterministic
            stress tests and reports whether a claim is robust, fragile, or suspicious.
          </p>
        </div>
        <VerdictBadge verdict={audit?.verdict} score={audit?.stability_score} />
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="workflow-grid">
        <Panel title="1. Dataset">
          <button className="primary-action" disabled={loading} onClick={handleLoadDemo}>
            Load synthetic demo dataset
          </button>
          {dataset && (
            <>
              <div className="metric-grid">
                <Metric label="Samples" value={dataset.quality.sample_count} />
                <Metric label="Features" value={dataset.quality.feature_count} />
                <Metric label="Missing" value={`${dataset.quality.missing_value_percentage.toFixed(1)}%`} />
              </div>
              <p className="hash-line">Dataset hash: {dataset.dataset_hash.slice(0, 18)}...</p>
              <MiniHeatmap dataset={dataset} />
            </>
          )}
        </Panel>

        <Panel title="2. Claim">
          <div className="template-row">
            {CLAIMS.map((template) => (
              <button key={template} className="chip" onClick={() => setClaim(template)}>
                {template}
              </button>
            ))}
          </div>
          <label className="field-label" htmlFor="claim">
            Claim to audit
          </label>
          <textarea id="claim" value={claim} onChange={(event) => setClaim(event.target.value)} />
          <label className="field-label" htmlFor="normalization">
            Normalization
          </label>
          <select
            id="normalization"
            value={normalization}
            onChange={(event) => setNormalization(event.target.value)}
          >
            {NORMALIZATIONS.map((variant) => (
              <option key={variant} value={variant}>
                {variant}
              </option>
            ))}
          </select>
          <div className="button-row">
            <button disabled={loading || !dataset} onClick={handleBaseline}>
              Run baseline
            </button>
            <button className="primary-action" disabled={loading || !dataset} onClick={handleAudit}>
              Audit claim
            </button>
          </div>
        </Panel>
      </section>

      <section className="results-grid">
        <Panel title="Baseline Analysis">
          {baseline ? (
            <>
              <div className="metric-grid">
                <Metric label="Subtypes" value={baseline.subtype_count} />
                <Metric label="Silhouette" value={baseline.silhouette_score.toFixed(3)} />
                <Metric label="WCSS" value={baseline.wcss.toFixed(1)} />
              </div>
              <ScatterPlot rows={baseline.pca} />
              <BiomarkerTable biomarkers={baseline.top_biomarkers} compact />
            </>
          ) : (
            <p className="placeholder">Run a baseline analysis to see the starting subtype structure.</p>
          )}
        </Panel>

        <Panel title="Claim Audit">
          {status && status.state !== "completed" && (
            <div className="progress-block">
              <div className="progress-header">
                <span>{status.phase}</span>
                <span>{progress}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p>{status.completed} of {status.total} perturbation steps completed.</p>
              {status.state === "failed" && <p className="error-text">{status.error}</p>}
            </div>
          )}

          {audit ? (
            <>
              <div className="metric-grid">
                <Metric label="Verdict" value={audit.verdict} />
                <Metric label="Stability" value={audit.stability_score.toFixed(3)} />
                <Metric label="Report" value={audit.report.paths?.json ? "Exported" : "Pending"} />
              </div>
              {audit.warnings.map((warning) => (
                <p key={warning} className="warning-line">{warning}</p>
              ))}
              <ScoreBars scores={audit.per_type_scores} />
              <BiomarkerTable biomarkers={audit.biomarkers} />
              {audit.report.paths?.json && (
                <p className="hash-line">Report: {audit.report.paths.json}</p>
              )}
            </>
          ) : (
            <p className="placeholder">Run the audit to see which parts of the claim survive stress tests.</p>
          )}
        </Panel>
      </section>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function VerdictBadge({ verdict, score }: { verdict?: string; score?: number }) {
  return (
    <div className={`verdict-badge ${verdict ?? "pending"}`}>
      <span>{verdict ?? "not audited"}</span>
      <strong>{score === undefined ? "--" : score.toFixed(3)}</strong>
    </div>
  );
}

function MiniHeatmap({ dataset }: { dataset: DatasetDescription }) {
  const values = dataset.preview.values.slice(0, 8).map((row) => row.slice(0, 18));
  const flat = values.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  return (
    <div className="mini-heatmap" aria-label="Dataset preview heatmap">
      {values.flatMap((row, rowIndex) =>
        row.map((value, colIndex) => {
          const t = (value - min) / Math.max(0.0001, max - min);
          return (
            <span
              key={`${rowIndex}-${colIndex}`}
              style={{ backgroundColor: `rgb(${Math.round(35 + t * 210)}, ${Math.round(80 + t * 90)}, ${Math.round(115 - t * 60)})` }}
            />
          );
        }),
      )}
    </div>
  );
}

function ScatterPlot({ rows }: { rows: BaselineResult["pca"] }) {
  if (!rows.length) return <p className="placeholder">No PCA rows returned.</p>;
  const width = 460;
  const height = 260;
  const xs = rows.map((row) => row.pc1);
  const ys = rows.map((row) => row.pc2);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const colors = ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626"];

  return (
    <svg className="plot" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="PCA projection">
      <rect width={width} height={height} rx="8" />
      {rows.map((row) => {
        const x = 24 + ((row.pc1 - minX) / Math.max(0.0001, maxX - minX)) * (width - 48);
        const y = 24 + ((row.pc2 - minY) / Math.max(0.0001, maxY - minY)) * (height - 48);
        return <circle key={row.sample_id} cx={x} cy={height - y} r="4" fill={colors[row.cluster % colors.length]} />;
      })}
    </svg>
  );
}

function ScoreBars({ scores }: { scores: Record<string, number> }) {
  return (
    <div className="score-bars">
      {Object.entries(scores).map(([name, score]) => (
        <div className="score-row" key={name}>
          <span>{name.replaceAll("_", " ")}</span>
          <div className="score-track">
            <div className={score < 0.5 ? "score-fill low" : "score-fill"} style={{ width: `${Math.max(0, Math.min(100, score * 100))}%` }} />
          </div>
          <strong>{score.toFixed(3)}</strong>
        </div>
      ))}
    </div>
  );
}

function BiomarkerTable({ biomarkers, compact = false }: { biomarkers: Array<{ feature: string; robustness_score: number; baseline_score: number; one_run_artifact: boolean }>; compact?: boolean }) {
  const rows = biomarkers.slice(0, compact ? 8 : 12);
  return (
    <table>
      <thead>
        <tr>
          <th>Feature</th>
          <th>{compact ? "Score" : "Robustness"}</th>
          {!compact && <th>Baseline</th>}
          {!compact && <th>Flag</th>}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.feature}>
            <td>{row.feature}</td>
            <td>{compact ? row.baseline_score.toFixed(2) : row.robustness_score.toFixed(2)}</td>
            {!compact && <td>{row.baseline_score.toFixed(2)}</td>}
            {!compact && <td>{row.one_run_artifact ? "one-run artifact" : "stable"}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}
