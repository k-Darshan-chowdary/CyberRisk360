# Phase 8 Security and Deployment Readiness

## Purpose and threat model

Phase 8 adds read-only integrity, quality, CI, and deployment-readiness controls to an educational Streamlit application. Protected assets are the fictional sample registers, source and configuration files, reporting behavior, and dependency declarations. The practical threats considered are accidental dataset changes, broken relationships, missing files, export regressions, unsafe configuration, unpinned dependencies, and routes that fail to start.

## Integrity and health architecture

Each sample CSV has a SHA-256 digest in `data/integrity_manifest.json`. `integrity_guard.py` validates safe project-relative manifest paths, calculates hashes in binary chunks, and compares files without modifying them. A legitimate CSV update requires review, tests, and intentional regeneration of the corresponding manifest digest. SHA-256 verifies byte consistency; it does not establish authenticity or safety by itself.

`project_health.py` checks required files, all five loaders, exact educational counts, case-insensitive register relationships, sample-data hashes, in-memory Markdown and seven-member ZIP exports, Streamlit settings, and dependency pins. Its fixed reference date makes results reproducible.

```text
Sample CSV Files
       |
       v
SHA-256 Integrity Manifest
       |
       v
Integrity Guard
       |
       +----------------------+
       |                      |
       v                      v
Relationship Checks     Export Checks
       |                      |
       +-----------+----------+
                   |
                   v
           Project Health Report
                   |
          +--------+---------+
          |                  |
          v                  v
   System Status Page   GitHub Actions CI
          |                  |
          +--------+---------+
                   |
                   v
          Deployment Readiness
```

## Quality gates

The Streamlit configuration keeps headless mode, XSRF protection, and CORS enabled; suppresses browser error details; and disables telemetry. Direct dependencies are pinned. Smoke tests exercise all routes without a permanent server. GitHub Actions uses minimum read permission and runs tests, the integrity guard, and all health checks. Git-ignore rules protect secrets, private keys, environments, caches, and generated exports.

The System Status page exposes neutral check results, protected-file status, a readiness checklist, and a Markdown preview. It performs no repairs and writes nothing.

## Deployment process and limitations

Release candidates must pass local and CI quality gates before the separate manual Streamlit Community Cloud procedure in `DEPLOYMENT.md`. Phase 8 does not include public deployment, real authentication, role-based authorization, a production database, penetration testing, a vulnerability-scanning service, secret-management integration, real financial data, or formal audit or certification.

These checks are deterministic regression and configuration checks, not adversarial penetration testing. They map no regulatory requirements and therefore are not evidence of formal compliance certification.
