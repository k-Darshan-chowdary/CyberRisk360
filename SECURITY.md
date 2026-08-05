# Security Policy

## Scope and supported version

CyberRisk360 is an educational portfolio application for a fictional organization. Only the current `main` branch is supported. All included data is fictional; the repository must never contain banking, customer, employee, personal, credential, or secret data.

Report a suspected security issue privately to the repository owner through GitHub. Do not publish vulnerability details before the owner has reviewed them. Do not include real sensitive information in a report.

## Security measures

The user interface is read-only and backend loaders validate sample inputs. SHA-256 verification detects changes to the five protected sample CSVs. Streamlit suppresses user-facing error details and enables XSRF protection and CORS. Direct dependencies are exactly pinned, and GitHub Actions runs tests, integrity verification, and health checks on changes to `main`.

No secrets are needed. Future secrets must be supplied through environment variables or Streamlit secrets and must not be committed; `.streamlit/secrets.toml`, environment files, keys, and certificates are ignored.

## Limitations

The project has no authentication, authorization, production database, durable audit log, encryption-at-rest implementation, vulnerability-scanning service, penetration test, or secret-management integration. Integrity hashes detect byte changes but do not prove a file is safe or trustworthy. There is no security warranty, compliance certification, or permission to use real banking data.
