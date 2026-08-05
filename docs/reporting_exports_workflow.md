# Phase 7 Reporting and Exports Workflow

## Purpose

Phase 7 turns the five CyberRisk360 registers into consistent management summaries, priority insights, and downloadable reports for the fictional EagleShield Community Bank. It remains read-only: source dictionaries, nested mapping lists, and CSV files are never edited by reporting or export operations.

Dashboards support interactive exploration inside Streamlit. Formal reports package the same deterministic information into portable Markdown, CSV, and ZIP formats that can be reviewed outside the application. Neither presentation establishes that the organization is secure or compliant.

The reporting reference date is **2026-08-05**. Using a fixed date makes evidence-expiration and remediation-overdue results reproducible in demonstrations and tests.

## Workflow

```text
Assets / Risks / Controls / Evidence / Remediation
                        |
                        v
                Reporting Engine
                        |
          +-------------+-------------+
          |                           |
          v                           v
  Management Insights          Export Manager
          |                           |
          v                           v
  Reports Streamlit Page   CSV / Markdown / ZIP
          |                           |
          +-------------+-------------+
                        |
                        v
              User Downloads Reports
```

## Reporting-engine architecture

`reporting_engine.py` is a pure-Python business-logic module. It does not depend on Streamlit or Pandas. Public functions validate top-level lists and dictionary records, reuse the existing evidence and remediation date helpers, and return new result collections.

- Risk summaries count residual ratings and open risks, average inherent and residual scores, and calculate average percentage reduction while safely handling a zero inherent score.
- Control summaries count implementation states case-insensitively and average effectiveness.
- Evidence-health summaries keep stored workflow status separate from calculated expiration. Evidence is classified as expired or expiring within 30 days relative to the reference date.
- Remediation summaries count statuses, reuse the register's overdue rule, and average completion.
- Relationship coverage counts unique, valid, case-insensitive links between parent registers. Duplicate and empty references do not inflate results.
- Priority selectors rank residual risks, find weak or incomplete controls, and preserve source order for evidence and remediation attention groups.
- `build_management_insights` composes those functions into one independent management model rather than duplicating calculations.

## In-memory exports

`export_manager.py` uses `StringIO` and `BytesIO`; it never opens a project output file.

- CSV exports retain each register's official field order. Control mapping lists are flattened into semicolon-separated display values. Evidence adds `calculated_condition`, and remediation adds `overdue`, without overwriting stored fields.
- Markdown generation creates an executive report with summaries, interpretations, coverage, priority tables, and scope notices. Empty priority sections receive readable messages rather than raw Python output.
- ZIP packaging uses `ZIP_DEFLATED` to combine the Markdown report, five CSV exports, and a manifest. Every member is generated and returned in memory.

The Streamlit Reports & Exports page calls these functions and passes their returned strings or bytes directly to uniquely keyed `st.download_button` widgets. This keeps report generation stateless and prevents download actions from changing backend data.

## Testing approach

Phase 7 tests load the existing sample registers and cover exact result keys, counts, averages, sorting, tie-breaking, case-insensitive relationships, validation, source-order preservation, deep-copy protection, exact CSV headers, calculated display columns, Markdown sections, ZIP membership, manifest content, and input immutability. The complete Phase 1–7 suite is run to catch regressions. Streamlit startup and page rendering are also checked.

## Current limitations

Phase 7 does not include:

- PDF generation
- Email distribution
- Scheduled reports
- Database storage
- Authentication
- Real financial data
- Editing backend records
- Production deployment

PDF generation is intentionally postponed until after Phase 8 so the final artifact can document the combined Phase 6–8 application and reporting experience once that scope is stable.
