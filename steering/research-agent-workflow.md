# Research-Agent Workflow

Use this workflow for cancer subtype, biomarker, SNP, expression, or omics hypothesis questions.

1. Start with `inspect_dataset` to capture sample count, feature count, quality warnings, and dataset hash.
2. Use `audit_biological_claim` for the claim. Do not skip perturbation testing.
3. Read `stability_score`, `per_type_scores`, `verdict`, and warnings before discussing markers.
4. Use `rank_robust_biomarkers` only as a post-audit marker triage step.
5. Use `generate_agent_findings` to convert computed evidence into cautious research findings.
6. In the final summary, separate computed evidence, literature evidence, and hypotheses.
7. Recommend independent-cohort validation and lab follow-up for any candidate marker.

For synthetic demo data, phrase markers as generated features, not as known genes.
