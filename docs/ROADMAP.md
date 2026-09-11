# CyberRisk360 roadmap

This roadmap separates implemented capabilities from proposed improvements.
Proposals are discussion areas, not scheduled releases or delivery commitments.
Use a feature request to describe a use case and agree on scope before starting
a substantial change.

## Current foundation

The repository implements a read-only GRC workflow using fictional data for
EagleShield Community Bank:

- Asset, risk, control, evidence, and remediation registers with input validation
  and relationship checks.
- Inherent and residual risk scoring using the documented likelihood, impact,
  and estimated control-effectiveness model.
- Nine Streamlit pages with summaries, filters, relationship views, and charts.
- CSV register downloads, an executive Markdown report, and a ZIP report package.
- Sample-data integrity verification, project-health checks, automated tests,
  and GitHub Actions quality gates.

See [the README](../README.md) for the current setup and limitations. The numbered
phase documents record how these capabilities were developed; earlier phase
scope statements do not describe the entire current application.

## Public launch preparation

Before announcing a release or linking a hosted demo:

- Make the project purpose, read-only workflow, and fictional-data scope clear in
  repository metadata and the README.
- Confirm the repository's licensing terms before describing a release as open
  source or inviting reuse under a specific license.
- Verify a clean Python 3.13 installation and all
  [contributor quality gates](../CONTRIBUTING.md#validate-a-change).
- Review screenshots and a short walkthrough of risk prioritization, control
  evidence, remediation, and executive reporting.
- Follow [deployment guidance](../DEPLOYMENT.md) if hosting a demo; verify every
  page and download before publishing its URL.
- Confirm that [the security policy](../SECURITY.md) has a usable reporting path.

## Proposed improvements

| Area | Candidate contribution | Evidence of completion |
| --- | --- | --- |
| Evaluation experience | Extend the [demo walkthrough](DEMO.md) with annotated screenshots and additional fictional risk scenarios. | Screenshots and steps match the current app and sample data. |
| Usability and accessibility | Review navigation, chart labels, keyboard interaction, and narrow layouts. | Documented findings and focused fixes with relevant manual checks. |
| Risk transparency | Add worked examples showing how risk-level effectiveness differs from control status and evidence freshness. | Worked examples agree with the backend calculations and reporting behavior. |
| Validation and regression coverage | Cover additional invalid-input cases and meaningful export or UI regressions. | Tests reproduce a concrete failure or protect a documented behavior. |
| Reporting | Improve report structure, field explanations, and consistency between pages and downloads. | Export checks and sample reports demonstrate the intended output. |
| Reproducibility | Investigate installation issues and keep dependency pins, setup instructions, and CI aligned. | A clean install runs the documented quality gates successfully. |

## Changes that need a separate design

Editable records, authentication and authorization, persistent storage, audit
history, real integrations, and automated evidence collection would materially
change the current architecture and data boundary. They require design proposals
and acceptance criteria before implementation; they are not current capabilities
or committed milestones.

Framework labels in sample records do not constitute a full framework assessment
or compliance certification. Production use with real organization data is
outside the current project scope.

Contributions can start with [CONTRIBUTING.md](../CONTRIBUTING.md) or an issue
describing a reproducible problem and the intended result.
