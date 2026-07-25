# Public Aggregate Results

This directory contains sanitized aggregate outputs from the approved v0.2.0 experiment matrix.

## Included

- `main_model_matrix.csv` — frozen v1 metrics for all approved model-condition pairs
- `main_model_matrix.md` — Markdown rendering of the same matrix
- `condition_comparison.csv` — condition-level comparison table
- `sensitivity_excluding_ambiguous.csv` — post-audit sensitivity metrics
- `sensitivity_excluding_ambiguous.md` — readable sensitivity table
- `manual_audit_summary.md` — preliminary audit counts and ambiguity finding
- `manifest.json` — approved experiment IDs and release metadata

## Excluded

The public aggregate directory intentionally excludes:

- API credentials
- `.env`
- Absolute local file paths
- Raw model responses
- Detailed audit worksheets
- Local process logs
- Personal application material

Raw traces remain ignored in the working repository until Ernest Boakye Danquah completes human review and approves a separate research-data release.

## Interpretation

The frozen v1 matrix includes all 15 scenarios. The sensitivity analysis excludes two scenarios identified post hoc as annotation-ambiguous. Both result layers must be reported together.

The results are preliminary, not peer reviewed, and apply only to the tested prompts, model identifiers, providers, and controlled mock traces.
