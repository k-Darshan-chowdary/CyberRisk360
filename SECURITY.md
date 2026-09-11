# Security Policy

## Scope and supported version

CyberRisk360 is a GRC reference application using a fictional organization and synthetic records. Security fixes target the current `main` branch; older snapshots have no separate maintenance commitment. The repository must never contain real banking, customer, employee, personal, credential, or secret data.

## Reporting a vulnerability

Open the repository's [Security tab](https://github.com/k-Darshan-chowdary/CyberRisk360/security) and use **Report a vulnerability** if GitHub private vulnerability reporting is enabled. Include the affected commit, impact, and minimal reproduction using synthetic data only.

If that option is unavailable, request a private reporting channel from the repository owner. A public issue requesting contact must contain no vulnerability details, exploit steps, credentials, or sensitive data. Do not send a detailed report until a private channel is available. Private reporting availability must be verified before public launch.

## Security measures

The user interface is read-only and backend loaders validate sample inputs. SHA-256 verification detects changes to the five protected sample CSVs. Streamlit suppresses user-facing error details and enables XSRF protection and CORS. Direct dependencies are exactly pinned, and GitHub Actions runs tests, integrity verification, and health checks on changes to `main`.

No secrets are needed. Future secrets must be supplied through environment variables or Streamlit secrets and must not be committed; `.streamlit/secrets.toml`, environment files, keys, and certificates are ignored.

## Limitations

The project has no authentication, authorization, production database, durable audit log, encryption-at-rest implementation, vulnerability-scanning service, penetration test, or secret-management integration. Integrity hashes detect byte changes but do not prove a file is safe or trustworthy. There is no security warranty, compliance certification, or permission to use real banking data.
