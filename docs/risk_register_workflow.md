# Phase 3 Risk Register Workflow

## Purpose

Phase 3 adds beginner-friendly CSV data management to CyberRisk360. The risk
register keeps risks in the existing Phase 1 format while providing Python
functions to load, find, search, filter, add, update, and delete records.

## Workflow

```text
User Risk Information
        |
        v
Input Validation
        |
        v
Asset Reference Check
        |
        v
Risk Scoring Engine
        |
        v
Risk Register CSV
        |
        v
Search / Filter / Update / Delete
```

## Loading and saving risks

`load_risks` reads the CSV with `csv.DictReader`, preserves row order, and
returns each row as a dictionary. Likelihood, impact, and inherent score become
integers. Control effectiveness and residual score become floats. Missing
columns and malformed values produce clear validation errors.

`save_risks` uses `csv.DictWriter`, includes the header, preserves record order,
and always writes the exact Phase 1 column order. Residual scores are written
with two decimal places. Saving creates output rows rather than changing the
list or dictionaries supplied by the caller.

## Register operations

- `get_risk_by_id` finds an ID without regard to letter case.
- `search_risks` searches IDs, titles, threats, vulnerabilities, assets,
  controls, and owners. A blank search returns every record.
- `filter_risks` applies optional status, inherent rating, residual rating,
  treatment, and NIST CSF function criteria. All supplied criteria must match.
- `add_risk` validates and scores a new record, rejects duplicate IDs, and
  appends the record to the CSV.
- `update_risk` keeps omitted fields, prevents ID changes, recalculates scores,
  and retains the record's original CSV position.
- `delete_risk` removes a matching record and preserves the order of the rest.

Lookup, search, filter, add, update, and delete results are copies, so callers
do not receive the internal dictionaries used during an operation.

## User-provided and calculated fields

Users provide the risk ID, title, threat, vulnerability, affected asset ID,
likelihood, impact, existing controls, control effectiveness percentage, risk
owner, treatment, status, target date, and NIST CSF function. Required text is
trimmed and cannot be blank. IDs, numeric ranges, allowed choices, and real ISO
dates are validated before a file is changed.

The register automatically calculates these fields:

- inherent score
- inherent rating
- residual score
- residual rating

Supplied calculated values cannot override the calculation. The register calls
`risk_engine.assess_risk`, reusing the tested Phase 2 scoring and rating rules
instead of maintaining a second scoring implementation.

## Asset reference validation

Every affected asset ID must follow the `AST-###` format. Add operations, and
updates that change the asset, read the supplied asset CSV and confirm that the
ID exists in its `asset_id` column. This prevents a risk from referring to an
unknown asset.

## Protecting sample data during tests

Write-operation tests use pytest's `tmp_path` fixture. Both sample CSV files are
copied into that temporary directory before add, update, delete, or save tests
run. The project copies in `data/` remain unchanged and continue to serve as
stable fictional examples.

## Phase 3 boundaries

Phase 3 does not include a Streamlit form, dashboard, database, or
authentication. Those concerns are outside this CSV data-management phase.
