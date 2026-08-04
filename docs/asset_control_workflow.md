# Asset Inventory and Security-Control Workflow

## Purpose

The asset inventory gives CyberRisk360 one consistent list of the fictional bank's systems, services, devices, owners, locations, data classifications, and business criticalities. It helps a beginner see what the organization needs to protect before evaluating risks or safeguards.

The security-control register records the safeguards used to manage those assets and risks. Each record describes a control, its owner, type, NIST Cybersecurity Framework (CSF) function, implementation status, effectiveness, mappings, review date, evidence reference, and notes.

## Asset inventory operations

`load_assets` reads and validates the asset CSV while preserving row order and string values. `get_asset_by_id` retrieves a single asset. `search_assets` checks IDs, names, types, owners, departments, locations, and descriptions. `filter_assets` supports exact, case-insensitive filtering by type, department, classification, criticality, and location.

`add_asset` validates and appends a unique asset. `update_asset` validates a complete updated record, preserves unchanged fields, and keeps its existing position. `delete_asset` removes an asset only if the risk register does not refer to it. These operations validate all data before saving, so rejected changes do not alter the CSV.

A referenced asset cannot be deleted because its removal would leave risks pointing to an asset that no longer exists. The deletion error identifies the related risk IDs so the relationship can be reviewed first.

## Control mappings and measurement

Controls can map to one or more assets, risks, or both. In Python, mappings are lists of IDs. In the CSV, multiple IDs are separated with semicolons. Every mapping is checked against the asset or risk register when a control is added or updated, and every control must have at least one mapping.

Effectiveness is stored as a percentage from 0 through 100 and written with two decimal places. It represents the estimated degree to which the control reduces or manages its mapped exposure; it is not proof that the control will always work. Review dates, evidence references, implementation status, and ownership make that estimate easier to revisit.

The register uses all six NIST CSF 2.0 functions: Govern, Identify, Protect, Detect, Respond, and Recover. A control has one primary function so users can group and filter the safeguards consistently.

## Workflow

```text
Assets CSV
    |
    v
Asset Inventory Management
    |
    +---------------------------+
    |                           |
    v                           v
Risk Register              Security Controls
    |                           |
    +------------+--------------+
                 |
                 v
       Asset / Risk Mapping
                 |
                 v
      Control Status and Effectiveness
```

## Testing and Phase 4 boundaries

Write tests copy the original asset, risk, and control samples into pytest temporary directories. Add, update, and delete tests operate only on those copies, protecting the project samples from test side effects.

Phase 4 provides CSV-backed Python modules, sample controls, tests, and this workflow documentation. It does not include:

- Streamlit forms
- A dashboard
- A database
- Authentication
- Evidence-file uploads
