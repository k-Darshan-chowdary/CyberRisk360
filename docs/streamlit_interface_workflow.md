# Phase 6 Streamlit Interface Workflow

## Purpose

Phase 6 turns the existing CyberRisk360 backend into a professional, beginner-friendly Streamlit application for EagleShield Community Bank. The interface presents the existing fictional GRC data through summary metrics, charts, searchable registers, filters, and relationship details.

The interface is intentionally read-only. This protects the validated sample data, keeps the phase focused on presentation and navigation, and preserves the backend behavior established in earlier phases.

## Application Flow

```text
CSV Files
    |
    v
Backend Load Functions
    |
    v
Cached UI Data Loader
    |
    v
Sidebar Navigation
    |
    +-------------------------------+
    |       |       |       |       |
    v       v       v       v       v
Dashboard Risks   Assets Controls Evidence
                            |
                            v
                       Remediation
```

The sidebar routes to the Executive Dashboard, Risk Register, Asset Inventory, Security Controls, Control Evidence, Remediation Actions, and About the Project pages. Routing remains in `app.py`; each page owns its presentation logic in the `ui` package.

## Centralized Data Loading and Caching

`ui/data_loader.py` is the single UI gateway to the sample CSV files. It defines paths relative to the project root and reuses the existing backend load functions, so the same validation and Python collection types apply in both layers.

Streamlit's `st.cache_data` caches each validated dataset in the UI layer. This avoids repeated disk reads during Streamlit reruns without coupling the backend modules to Streamlit. `clear_project_data_cache()` clears these UI caches and never writes to a CSV file.

Missing files continue to raise `FileNotFoundError`, while malformed records raise clear validation errors. The main application converts these failures into friendly user messages; an optional developer expander is used only for unexpected errors.

## Dashboard Metrics and Charts

The Executive Dashboard summarizes assets, risks, residual risk ratings, controls, evidence, and remediation work. It charts residual ratings, NIST CSF functions, control implementation status, and remediation status. Priority Attention tables highlight high-impact residual risks, evidence expiration, and overdue actions.

Evidence expiration and remediation overdue calculations use the fixed reference date `2026-08-05` so portfolio demonstrations and tests remain deterministic.

## Search and Filter Flow

Each register page follows the same simple flow:

1. Load validated records from the central UI loader.
2. Pass the user's search text to the existing backend search function.
3. Pass those search results to the existing backend filter function.
4. Copy the filtered records into a pandas DataFrame for display.
5. Show a filtered count, a read-only table, or a helpful empty-result message.

Reset buttons clear only the relevant Streamlit widget state. Search and filters can be combined, and no filter changes the underlying records.

## Detail Views and Relationships

The Asset Inventory detail view shows the selected asset, risks affecting it, and controls mapped to it. The Security Controls detail view shows the selected control, its evidence, and its remediation actions. These views reuse backend relationship helpers where available and expose the cross-module structure of a GRC program.

Mapped identifier lists are converted to comma-separated text only in copied display records. Evidence condition and remediation overdue columns are also calculated on copies. Stored status fields are not overwritten.

## Why Pandas Is Limited to the UI

Backend register functions continue to accept and return standard Python lists and dictionaries. Pandas is used only to shape copied data for readable Streamlit tables. This separation keeps business logic easy to test, avoids changing caller-owned data, and ensures a UI concern does not become a backend dependency.

## Data Preservation and Error Handling

The UI calls only backend read functions. It does not call save, add, update, or delete functions. Cached data is returned for presentation, nested lists are formatted on deep copies, and derived display columns are never written back to CSV.

If a required CSV is missing or invalid, the application displays a concise action-oriented message instead of a raw traceback. Empty datasets and empty filter results receive helpful messages rather than blank tables.

## Current Limitations

Phase 6 does not include:

- Add forms
- Edit forms
- Delete buttons
- Authentication
- Database storage
- File uploads
- Email alerts
- Production deployment

The organization, systems, people, risks, and records are fictional. No real banking or personal data is used.
