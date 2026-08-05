# Deployment Readiness

Phase 8 prepares CyberRisk360 for deployment but does not deploy it. Public deployment is a separate manual decision. Never upload real banking, customer, employee, or personal information.

## Prerequisites and local gates

Use Git, a GitHub repository, and Python 3.13 to match development. From Windows CMD, create and activate a virtual environment, then install `requirements.txt`. The entry point is `app.py`; Streamlit configuration is stored at `.streamlit/config.toml`.

Run every quality gate before release:

```bat
python -m pytest -q
python integrity_guard.py
python project_health.py
python -m streamlit run app.py
```

Confirm all nine pages render, the System Status page is Healthy, downloads are available, and no CSV changes appear in Git.

## Streamlit Community Cloud

1. Push an approved commit to the GitHub repository's `main` branch.
2. In Streamlit Community Cloud, create an app and select the repository, `main` branch, and `app.py`.
3. In advanced settings, select Python 3.13.
4. No secrets are required for this fictional read-only version.
5. Deploy only after the separate manual approval decision.

After deployment, open every route, review System Status, exercise downloads, and inspect application logs for import, configuration, or resource errors. Community Cloud has resource limits, so monitor startup time and memory use.

## Rollback and monitoring

Monitor Streamlit logs and GitHub Actions after changes. To roll back, identify the last known-good GitHub commit, revert the faulty commit in a reviewed pull request, rerun all gates, and allow Community Cloud to redeploy `main`. Do not bypass integrity failures.

The current design has no authentication, authorization, production database, audit-log storage, penetration test, formal certification, or suitability for real financial data.
