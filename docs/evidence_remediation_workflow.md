# Evidence and Remediation Workflow

## Purpose

Control evidence gives reviewers a traceable reason to conclude that a security control exists and is operating as described. Examples include configurations, reports, attestations, test results, and procedures. CyberRisk360 records evidence metadata and a storage reference; it does not store the evidence file itself.

Remediation actions turn an identified control gap or risk treatment decision into accountable work. Each action records what must change, who owns it, its urgency, its deadline, its progress, and how completion will be verified.

## Workflow

```text
Security Control
       |
       v
Control Evidence
       |
       +------------------+
       |                  |
       v                  v
Evidence Review      Gap Identified
                          |
                          v
                  Remediation Action
                          |
                          v
             Owner / Priority / Due Date
                          |
                          v
                Verification and Closure
```

## Evidence lifecycle and control mapping

Evidence is collected, assigned to exactly one valid security control, and given an owner and storage reference. A reviewer evaluates it on the review date. Its status can show that it is current, approaching expiration, expired, under review, or rejected. The expiration date supports repeatable checks: evidence is expired only after that date, while the expiring-evidence query includes items expiring today through the final day of a selected window.

Mapping by `control_id` connects the proof to the safeguard it supports. Reviewers can retrieve all evidence for a control, search descriptive metadata, or filter by type, status, owner, and reviewer. A storage reference such as a fictional GRC path tells a user where the separate artifact would be retained.

## Remediation tracking and relationships

Every remediation action maps to at least one valid risk or control. An action can map to both when a control improvement directly treats a recorded risk, or to only one when that is the clearest relationship. Priority communicates urgency; status communicates workflow state; the action owner and due date establish accountability; and `completion_pct` reports progress from 0 through 100.

Completed and closed actions must be at 100 percent. Closed actions also require a closure date. Verification notes record the fictional review used to support completion or closure. An active action becomes overdue after its due date, but not on the due date itself. Closed and cancelled actions are never classified as overdue.

## Safe testing

Write tests copy the sample CSV files into pytest `tmp_path` directories before adding, updating, or deleting records. The tests therefore exercise real file behavior without changing the portfolio's original fictional sample data. Failed validation is performed before saving so an invalid operation also leaves its temporary register unchanged.

## Phase 5 boundaries

Phase 5 deliberately does not include:

- File uploads
- Email notifications
- Streamlit forms
- A dashboard
- A database
- Authentication

Those capabilities can be considered separately in a later phase. Phase 5 is limited to readable, standard-library Python modules, fictional CSV data, automated tests, and this workflow explanation.
