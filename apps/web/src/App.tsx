import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  getAuditResult,
  getAgentFindings,
  getJobStatus,
  getKiroExplanation,
  getLiteratureEvidence,
  getReport,
  getReportHtml,
  loadDemoDataset,
  runBaseline,
  startAudit,
  uploadDataset,
} from "./api";
import type {
  AgentFindings,
  AuditResult,
  BaselineResult,
  BiomarkerRank,
  DatasetDescription,
  JobStatus,
  KiroVerdictExplanation,
  LiteratureEvidence,
  ReproducibilityReport,
} from "./types";

const CLAIMS = [
  "These samples form three stable subtypes.",
  "These genes distinguish subtype A from subtype B.",
  "These biomarkers are stable across cohorts.",
];

const NORMALIZATIONS = ["z-score", "log2", "quantile", "none"];
const PROHIBITED_TERMS = [
  "diagnostic",
  "clinically proven",
  "clinical validation",
  "FDA approved",
  "patient diagnosis",
  "treatment recommendation",
];

export function App() {
  const [dataset, setDataset] = useState<DatasetDescription | null>(null);
  const [claim, setClaim] = useState(CLAIMS[0]);
  const [normalization, setNormalization] = useState("z-score");
  const [baseline, setBaseline] = useState<BaselineResult | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [agentFindings, setAgentFindings] = useState<AgentFindings | null>(null);
  const [kiroExplanation, setKiroExplanation] = useState<KiroVerdictExplanation | null>(null);
  const [report, setReport] = useState<ReproducibilityReport | null>(null);
  const [expressionFile, setExpressionFile] = useState<File | null>(null);
  const [metadataFile, setMetadataFile] = useState<File | null>(null);
  const [literatureMarker, setLiteratureMarker] = useState("");
  const [literatureContext, setLiteratureContext] = useState("cancer subtype biomarker");
  const [literature, setLiterature] = useState<LiteratureEvidence | null>(null);
  const [literatureLoading, setLiteratureLoading] = useState(false);
  const [agentFindingsLoading, setAgentFindingsLoading] = useState(false);
  const [kiroLoading, setKiroLoading] = useState(false);
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
          void handleKiroExplanation(next.job_id);
          void handleAgentFindings(next.job_id);
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
      setBaseline(null);
      setAudit(null);
      setAgentFindings(null);
      setKiroExplanation(null);
      setReport(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    if (!expressionFile) {
      setError("Choose a CSV or TSV expression matrix before uploading.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      setDataset(await uploadDataset(expressionFile, metadataFile));
      setBaseline(null);
      setAudit(null);
      setAgentFindings(null);
      setKiroExplanation(null);
      setReport(null);
      setStatus(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function assertAllowedClaim() {
    const lower = claim.toLowerCase();
    const matches = PROHIBITED_TERMS.filter((term) => lower.includes(term.toLowerCase()));
    if (matches.length) {
      throw new Error(`Clinical interpretation language is not supported: ${matches.join(", ")}.`);
    }
  }

  async function handleBaseline() {
    setError(null);
    setAudit(null);
    setAgentFindings(null);
    setKiroExplanation(null);
    setReport(null);
    setStatus(null);
    setLoading(true);
    try {
      assertAllowedClaim();
      setBaseline(await runBaseline(dataset?.dataset_id ?? "demo", claim, normalization));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAudit() {
    setError(null);
    setAudit(null);
    setAgentFindings(null);
    setKiroExplanation(null);
    setReport(null);
    setLoading(true);
    try {
      assertAllowedClaim();
      const job = await startAudit(dataset?.dataset_id ?? "demo", claim, normalization);
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

  async function handleFetchReport() {
    const reportId = audit?.report.report_id;
    if (!reportId) return;
    setError(null);
    try {
      const nextReport = await getReport(reportId);
      setReport(nextReport);
      downloadJson(`${reportId}.json`, nextReport);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleFetchHtmlReport() {
    const reportId = audit?.report.report_id;
    if (!reportId) return;
    setError(null);
    try {
      const html = await getReportHtml(reportId);
      downloadText(`${reportId}.html`, html, "text/html");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleKiroExplanation(jobId = status?.job_id) {
    if (!jobId) return;
    setKiroLoading(true);
    try {
      setKiroExplanation(await getKiroExplanation(jobId));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setKiroLoading(false);
    }
  }

  async function handleAgentFindings(jobId = status?.job_id) {
    if (!jobId) return;
    setAgentFindingsLoading(true);
    try {
      setAgentFindings(await getAgentFindings(jobId));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setAgentFindingsLoading(false);
    }
  }

  async function handleLiteratureSearch(markerOverride?: string) {
    const marker = (markerOverride ?? literatureMarker).trim();
    if (!marker) {
      setError("Enter a marker before checking literature evidence.");
      return;
    }
    setError(null);
    setLiteratureLoading(true);
    try {
      const evidence = await getLiteratureEvidence(marker, literatureContext, 5);
      setLiterature(evidence);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLiteratureLoading(false);
    }
  }

  function handleSelectBiomarker(feature: string) {
    setLiteratureMarker(feature);
    void handleLiteratureSearch(feature);
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
          <div className="upload-box">
            <label>
              <span>Expression matrix</span>
              <input
                type="file"
                accept=".csv,.tsv,.tab,text/csv,text/tab-separated-values"
                onChange={(event) => setExpressionFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <label>
              <span>Metadata optional</span>
              <input
                type="file"
                accept=".csv,.tsv,.tab,text/csv,text/tab-separated-values"
                onChange={(event) => setMetadataFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <button disabled={loading || !expressionFile} onClick={handleUpload}>
              Upload dataset
            </button>
          </div>
          {dataset && (
            <>
              <div className="metric-grid">
                <Metric label="Samples" value={dataset.quality.sample_count} />
                <Metric label="Features" value={dataset.quality.feature_count} />
                <Metric label="Missing" value={`${dataset.quality.missing_value_percentage.toFixed(1)}%`} />
              </div>
              <p className="hash-line">Dataset hash: {dataset.dataset_hash.slice(0, 18)}...</p>
              {dataset.metadata && (
                <p className="hash-line">
                  Metadata: {dataset.metadata.index.length} samples with {dataset.metadata.columns.length} fields.
                </p>
              )}
              <QualityDetails quality={dataset.quality} />
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
              <ResultHeatmap heatmap={baseline.heatmap} />
              <BiomarkerTable biomarkers={baseline.top_biomarkers} compact onSelect={handleSelectBiomarker} />
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
              <AuditDecisionCard audit={audit} agentFindings={agentFindings} />
              <div className="metric-grid">
                <Metric label="Verdict" value={audit.verdict} />
                <Metric label="Stability" value={audit.stability_score.toFixed(3)} />
                <Metric label="Report" value={audit.report.paths?.json ? "Exported" : "Pending"} />
              </div>
              {audit.warnings.map((warning) => (
                <p key={warning} className="warning-line">{warning}</p>
              ))}
              <ScoreBars scores={audit.per_type_scores} />
              {kiroExplanation ? (
                <KiroExplanationCard explanation={kiroExplanation} />
              ) : (
                <div className="kiro-explanation-empty">
                  <p className="placeholder">
                    Kiro can explain this verdict from the computed audit evidence without changing it.
                  </p>
                  <button disabled={kiroLoading || !status?.job_id} onClick={() => void handleKiroExplanation()}>
                    {kiroLoading ? "Generating..." : "Generate Kiro explanation"}
                  </button>
                </div>
              )}
              {agentFindings ? (
                <AgentFindingsCard findings={agentFindings} />
              ) : (
                <div className="agent-findings-empty">
                  <p className="placeholder">
                    The research agent can convert the completed audit into evidence-backed findings.
                  </p>
                  <button disabled={agentFindingsLoading || !status?.job_id} onClick={() => void handleAgentFindings()}>
                    {agentFindingsLoading ? "Generating..." : "Generate agent findings"}
                  </button>
                </div>
              )}
              <BiomarkerTable biomarkers={audit.biomarkers} onSelect={handleSelectBiomarker} />
              {audit.report.paths?.json && (
                <p className="hash-line">Report: {audit.report.paths.json}</p>
              )}
              {audit.report.report_id && (
                <div className="button-row">
                  <button onClick={handleFetchReport}>Download report JSON</button>
                  <button onClick={handleFetchHtmlReport}>Download report HTML</button>
                </div>
              )}
              {report && (
                <p className="hash-line">Downloaded report {report.report_id} with verdict {report.claim_verdict}.</p>
              )}
            </>
          ) : (
            <p className="placeholder">Run the audit to see which parts of the claim survive stress tests.</p>
          )}
        </Panel>

        <Panel title="Literature Evidence">
          <div className="literature-form">
            <label htmlFor="literature-marker">
              <span>Marker</span>
              <input
                id="literature-marker"
                value={literatureMarker}
                placeholder="TP53"
                onChange={(event) => setLiteratureMarker(event.target.value)}
              />
            </label>
            <label htmlFor="literature-context">
              <span>Context</span>
              <input
                id="literature-context"
                value={literatureContext}
                onChange={(event) => setLiteratureContext(event.target.value)}
              />
            </label>
            <button disabled={literatureLoading} onClick={() => void handleLiteratureSearch()}>
              {literatureLoading ? "Checking..." : "Check literature"}
            </button>
          </div>
          {literature ? (
            <LiteratureEvidenceCard evidence={literature} />
          ) : (
            <p className="placeholder">Select a biomarker or enter a marker symbol.</p>
          )}
        </Panel>
      </section>
    </main>
  );
}

function ResultHeatmap({ heatmap }: { heatmap?: BaselineResult["heatmap"] }) {
  if (!heatmap || !heatmap.values.length) {
    return <p className="placeholder">No heatmap data returned.</p>;
  }
  const rows = heatmap.values.slice(0, 30);
  const flat = rows.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  return (
    <div
      className="result-heatmap"
      aria-label="Top variable feature heatmap"
      style={{ gridTemplateColumns: `repeat(${rows[0]?.length ?? 1}, minmax(2px, 1fr))` }}
    >
      {rows.flatMap((row, rowIndex) =>
        row.map((value, colIndex) => {
          const t = (value - min) / Math.max(0.0001, max - min);
          return (
            <span
              key={`${rowIndex}-${colIndex}`}
              title={`${heatmap.features[rowIndex]} / ${heatmap.samples[colIndex]}: ${value.toFixed(2)}`}
              style={{
                backgroundColor: `rgb(${Math.round(30 + t * 210)}, ${Math.round(65 + t * 110)}, ${Math.round(145 - t * 70)})`,
              }}
            />
          );
        }),
      )}
    </div>
  );
}

function QualityDetails({ quality }: { quality: DatasetDescription["quality"] }) {
  const topWarnings = quality.warnings.slice(0, 3);
  const topFeatures = quality.feature_summaries
    .slice()
    .sort((a, b) => b.zero_value_percentage - a.zero_value_percentage || a.std - b.std)
    .slice(0, 4);

  return (
    <div className="quality-block">
      {topWarnings.length > 0 ? (
        topWarnings.map((warning) => (
          <p className="warning-line" key={warning}>
            {warning}
          </p>
        ))
      ) : (
        <p className="hash-line">No high-missingness or low-variation warnings detected.</p>
      )}
      <div className="feature-summary-grid">
        {topFeatures.map((feature) => (
          <div key={feature.feature}>
            <strong>{feature.feature}</strong>
            <span>std {feature.std.toFixed(2)}</span>
            <span>zero {feature.zero_value_percentage.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
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

function AuditDecisionCard({ audit, agentFindings }: { audit: AuditResult; agentFindings: AgentFindings | null }) {
  const weakest = weakestPerturbation(audit.per_type_scores);
  const artifactCount = audit.biomarkers.filter((marker) => marker.one_run_artifact).length;
  const stableMarkers = audit.biomarkers.filter((marker) => !marker.one_run_artifact).slice(0, 3);
  const decision = researchDecision(audit.verdict, artifactCount);
  const agentFinding = agentFindings?.findings[0];

  return (
    <div className={`decision-panel ${audit.verdict}`}>
      <div className="decision-header">
        <span>Research decision</span>
        <strong>{decision.title}</strong>
        <p>{decision.body}</p>
      </div>
      <div className="decision-grid">
        <div>
          <span>What survived</span>
          <strong>{audit.stability_score.toFixed(3)} stability</strong>
          <p>
            The subtype claim survived {Object.keys(audit.per_type_scores).length} stress-test classes.
            {stableMarkers.length
              ? ` Stable marker leads: ${stableMarkers.map((marker) => marker.feature).join(", ")}.`
              : " Marker-level evidence still needs review."}
          </p>
        </div>
        <div>
          <span>What broke</span>
          <strong>{artifactCount} artifact flags</strong>
          <p>
            {weakest
              ? `${weakest.name.replaceAll("_", " ")} was the weakest perturbation at ${weakest.score.toFixed(3)}.`
              : "No weak perturbation class was returned."}
            {audit.warnings.length ? ` ${audit.warnings[0]}` : ""}
          </p>
        </div>
        <div>
          <span>Next validation step</span>
          <strong>{decision.nextLabel}</strong>
          <p>{agentFinding?.recommended_next_step ?? decision.nextStep}</p>
        </div>
      </div>
    </div>
  );
}

function researchDecision(verdict: AuditResult["verdict"], artifactCount: number) {
  if (verdict === "fragile") {
    return {
      title: "Do not trust yet",
      body: "The claim failed the stability threshold. Treat it as an unvalidated hypothesis.",
      nextLabel: "Rework claim",
      nextStep: "Inspect the weakest perturbation, revise preprocessing, and rerun before presenting the result.",
    };
  }
  if (verdict === "suspicious") {
    return {
      title: "Investigate before claiming",
      body: "The claim has partial support but did not clear the robust threshold.",
      nextLabel: "Stress-test again",
      nextStep: "Review perturbation failures and validate the claim on another cohort before using it in a research story.",
    };
  }
  if (artifactCount > 0) {
    return {
      title: "Proceed with caution",
      body: "The subtype claim is stable, but some downstream marker candidates are not reproducible enough yet.",
      nextLabel: "Validate markers",
      nextStep: "Keep the subtype claim as a lead, down-rank one-run artifacts, and validate stable markers in an independent cohort.",
    };
  }
  return {
    title: "Proceed to validation",
    body: "The claim cleared the robust threshold and returned no marker artifact flags in the reviewed set.",
    nextLabel: "External cohort",
    nextStep: "Export the report and test the claim on an independent cohort before making a research claim.",
  };
}

function weakestPerturbation(scores: Record<string, number>) {
  const entries = Object.entries(scores);
  if (!entries.length) return null;
  const [name, score] = entries.reduce((weakest, current) => (current[1] < weakest[1] ? current : weakest));
  return { name, score };
}

function KiroExplanationCard({ explanation }: { explanation: KiroVerdictExplanation }) {
  return (
    <div className="kiro-explanation">
      <div>
        <span className="kiro-label">Kiro explanation</span>
        <h3>{explanation.headline}</h3>
        <p>{explanation.summary}</p>
      </div>
      <div className="kiro-evidence-grid">
        {explanation.evidence.map((item) => (
          <div key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.interpretation}</p>
          </div>
        ))}
      </div>
      <div className="kiro-list-grid">
        <div>
          <h4>Reasoning path</h4>
          <ul>
            {explanation.reasoning_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Next checks</h4>
          <ul>
            {explanation.next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
      </div>
      <p className="hash-line">
        Kiro role: {explanation.kiro_role}. Verdict source: {explanation.verdict_source.replaceAll("_", " ")}.
      </p>
    </div>
  );
}

function AgentFindingsCard({ findings }: { findings: AgentFindings }) {
  const markerEvidence = findings.evidence_snapshot?.marker_evidence ?? [];
  return (
    <div className="agent-findings">
      <div>
        <span className="agent-label">Research agent</span>
        <h3>{findings.headline}</h3>
        <p>{findings.executive_summary}</p>
        <p className="hash-line">
          Mode: {findings.mode.replaceAll("_", " ")} · Provider: {findings.provider} · Model: {findings.model}
        </p>
      </div>
      <div className="agent-finding-list">
        {findings.findings.map((finding) => (
          <article key={`${finding.finding_type}-${finding.title}`}>
            <div>
              <span>{finding.finding_type.replaceAll("_", " ")}</span>
              <strong>{finding.confidence}</strong>
            </div>
            <h4>{finding.title}</h4>
            <p>{finding.evidence}</p>
            <p>{finding.interpretation}</p>
            <p className="hash-line">Next: {finding.recommended_next_step}</p>
          </article>
        ))}
      </div>
      {markerEvidence.length > 0 && (
        <div className="research-gap-strip">
          {markerEvidence.slice(0, 5).map((marker) => (
            <div key={marker.feature}>
              <span>{marker.feature}</span>
              <strong>{marker.research_gap_score}/100</strong>
              <small>{marker.literature.evidence_level}</small>
            </div>
          ))}
        </div>
      )}
      <details className="agent-trace">
        <summary>Agent trace and guardrails</summary>
        <div className="kiro-list-grid">
          <div>
            <h4>Trace</h4>
            <ul>
              {findings.agent_trace.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Guardrails</h4>
            <ul>
              {findings.guardrails.map((guardrail) => (
                <li key={guardrail}>{guardrail}</li>
              ))}
            </ul>
          </div>
        </div>
      </details>
    </div>
  );
}

function BiomarkerTable({
  biomarkers,
  compact = false,
  onSelect,
}: {
  biomarkers: BiomarkerRank[];
  compact?: boolean;
  onSelect?: (feature: string) => void;
}) {
  const rows = biomarkers.slice(0, compact ? 8 : 12);
  return (
    <table>
      <thead>
        <tr>
          <th>Feature</th>
          <th>{compact ? "Score" : "Robustness"}</th>
          {!compact && <th>Baseline</th>}
          {!compact && <th>Flag</th>}
          {onSelect && <th>Evidence</th>}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.feature}>
            <td>{row.feature}</td>
            <td>{compact ? row.baseline_score.toFixed(2) : row.robustness_score.toFixed(2)}</td>
            {!compact && <td>{row.baseline_score.toFixed(2)}</td>}
            {!compact && <td>{row.one_run_artifact ? "one-run artifact" : "stable"}</td>}
            {onSelect && (
              <td>
                <button className="table-action" onClick={() => onSelect(row.feature)}>
                  Check
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function LiteratureEvidenceCard({ evidence }: { evidence: LiteratureEvidence }) {
  return (
    <div className="literature-card">
      <div className="metric-grid">
        <Metric label="Evidence" value={evidence.evidence_level} />
        <Metric label="PubMed hits" value={evidence.total_hits} />
        <Metric label="Reviewed" value={evidence.works_examined} />
      </div>
      <p className={evidence.status === "ok" ? "hash-line" : "warning-line"}>{evidence.summary}</p>
      <p className="hash-line">Query: {evidence.query}</p>
      {evidence.hits.length > 0 && (
        <div className="literature-hits">
          {evidence.hits.map((hit) => (
            <a key={hit.url} href={hit.url} target="_blank" rel="noreferrer">
              <strong>{hit.title}</strong>
              <span>
                {hit.journal} · {hit.year}
                {hit.authors.length ? ` · ${hit.authors.join(", ")}` : ""}
              </span>
            </a>
          ))}
        </div>
      )}
      {evidence.caveats.map((caveat) => (
        <p className="hash-line" key={caveat}>
          {caveat}
        </p>
      ))}
    </div>
  );
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}

function downloadJson(filename: string, data: unknown) {
  downloadText(filename, JSON.stringify(data, null, 2), "application/json");
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
