# Contributing to CyberRisk360

CyberRisk360 connects assets, risks, controls, evidence, and remediation in a
read-only GRC application. Contributions should make that workflow easier to
understand, more reliable, or easier to evaluate using fictional data.

Start with the [README](README.md), [risk methodology](docs/risk_methodology.md),
and [data dictionary](docs/data_dictionary.md). The [roadmap](docs/ROADMAP.md)
lists areas for discussion. Before a substantial change to scoring, data schemas,
dependencies, or architecture, open a feature request describing the problem and
proposed behavior. Small documentation fixes can go directly to a pull request.

For suspected vulnerabilities, follow [SECURITY.md](SECURITY.md) rather than
posting details in a public issue or pull request.

## Set up a development environment

Use Python 3.13 to match [CI](.github/workflows/ci.yml). Fork the repository on
GitHub, clone your fork, and create a branch for your change. From the repository
root, create a virtual environment:

```text
python -m venv .venv
```

Activate it using the command for your shell:

| Shell | Command |
| --- | --- |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| macOS / Linux bash or zsh | `source .venv/bin/activate` |

Install the pinned dependencies and run the app:

```text
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Useful contribution areas

- **Documentation:** clarify setup, risk-scoring examples, relationships, and the
  distinction between current capabilities and proposed work.
- **Interface:** improve navigation, chart labels, keyboard access, and clarity
  of the read-only workflow.
- **Validation:** improve error handling and coverage for invalid inputs, dates,
  IDs, and relationships between registers.
- **Reporting:** improve the readability and consistency of the executive report,
  CSV registers, and ZIP package.
- **Reproducibility:** investigate installation problems and keep the documented
  setup aligned with CI.

Use focused changes and follow the style of nearby code. Keep scoring logic in
the backend modules rather than duplicating it in the UI. Add or update tests
when behavior changes; documentation-only edits usually need a link and content
review instead.

## Data and methodology changes

Use only fictional records in code, screenshots, reports, tests, and issue
attachments. Do not include real organization records, personal information,
credentials, or secrets.

The five `data/sample_*.csv` files are verified against
`data/integrity_manifest.json`. For an intentional sample change:

1. Explain the scenario and preserve valid IDs, relationships, and CSV schemas.
2. Keep LF line endings, as required by `.gitattributes`.
3. Update affected documentation and tests. If sample counts change, update the
   expected counts in `project_health.py` and their tests as part of the same PR.
4. Calculate the SHA-256 digest of each changed file with
   `integrity_guard.calculate_file_sha256` and update only the corresponding
   manifest entries after reviewing the data changes.
5. Run all quality gates. Investigate an unexpected hash mismatch before
   changing the manifest; the checker is read-only and does not regenerate it.

For scoring changes, include worked examples and update
[the methodology](docs/risk_methodology.md). Framework labels describe the sample
data; they do not establish compliance or certification.

## Validate a change

Run these commands from the repository root with the virtual environment active:

```text
python -m pytest -q
python integrity_guard.py
python project_health.py
```

These are the same gates used by CI. Record any failure with its reproduction
steps instead of presenting a partial run as a pass.

For UI or export changes, also run the app, visit the affected pages, and exercise
the relevant filters and downloads. The automated Streamlit smoke tests cover all
nine routes; a manual review is still useful for readability and chart layout.
Confirm that viewing pages and downloading reports leave the sample CSV files
unchanged.

## Submit a pull request

Target `main` and use the PR template to explain the problem, resulting behavior,
and validation performed. Link the relevant issue if there is one. Include a
screenshot for a visible UI change, using fictional data only. Keep unrelated
refactors separate so the change can be reviewed on its own.

Be specific and respectful in issues and reviews. Describe the behavior you
observed and the outcome you need; avoid sharing sensitive information in logs
or screenshots.
