# CyberRisk360

CyberRisk360 is a beginner-friendly cybersecurity Governance, Risk, and Compliance portfolio application for **EagleShield Community Bank**, a fictional organization. All records are fictional and intended only for education and demonstration.

## Purpose and features

The project demonstrates an end-to-end GRC workflow: asset inventory, inherent and residual risk scoring, control mapping, evidence tracking, remediation management, executive reporting, integrity verification, and deployment-readiness checks. Its read-only Streamlit interface provides dashboards, filters, relationship views, charts, Markdown/CSV/ZIP downloads, and a technical System Status page.

```text
Sample CSV Data
       |
       v
Backend Register Modules
       |
       v
Validation and Business Logic
       |
       +-------------------------+
       |                         |
       v                         v
Reporting Engine          Integrity Guard
       |                         |
       v                         v
Export Manager            Project Health
       |                         |
       +------------+------------+
                    |
                    v
             Streamlit Interface
                    |
          +---------+---------+
          |                   |
          v                   v
 Dashboards and Tables   Reports and Status
```

## Completed phases

Phases 0 through 8 cover foundation and scope, risk methodology and register, asset/control relationships, evidence, remediation, the Streamlit interface, reporting/exports, and security hardening with deployment readiness.

## Architecture and pages

Main modules are `risk_engine.py`, the five `*_register.py` modules, `reporting_engine.py`, `export_manager.py`, `integrity_guard.py`, and `project_health.py`. Nine pages cover Executive Dashboard, Risk Register, Asset Inventory, Security Controls, Control Evidence, Remediation Actions, Reports & Exports, System Status, and About the Project.

Inherent risk is likelihood × impact. Residual risk reduces inherent risk by the validated control-effectiveness percentage, after which consistent rating bands are applied.

The sample contains 8 assets, 10 risks, 12 controls, 12 evidence records, and 10 remediation actions. Exports include five CSV registers, an executive Markdown report, and a seven-member in-memory ZIP package.

## Integrity, health, and testing

SHA-256 protects all five sample CSV files. Eight project-health checks cover required files, loading, counts, relationships, integrity, reporting/exports, Streamlit configuration, and exact dependency pins. Pytest includes backend, reporting, integrity, health, and Streamlit route regression coverage. GitHub Actions repeats the quality gates for pushes and pull requests involving `main`.

## Local installation and use

The development environment uses Python 3.13. In Windows CMD:

```bat
git clone <repository-url>
cd CyberRisk360
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Run the gates independently:

```bat
python -m pytest -q
python integrity_guard.py
python project_health.py
```

Use a feature branch, commit focused changes, push the branch, and open a pull request targeting `main`. Review the diff and require CI to pass before merge. Never commit secrets or real data.

## Deployment and security status

Phase 8 prepares the application for manual deployment but does not publicly deploy it. See [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md), and [the Phase 8 design](docs/security_deployment_readiness.md). The project is not formally compliant, certified, penetration-tested, or production-ready for real financial data.

Technologies: Python 3.13, Streamlit, Pandas, Plotly, Pytest, Git, GitHub Actions, CSV, JSON, TOML, Markdown, and ZIP.

No authentication, authorization, production database, durable audit log, encryption-at-rest implementation, or warranty is provided. Do not use or upload real banking or personal information.
