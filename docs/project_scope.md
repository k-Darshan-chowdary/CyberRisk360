# CyberRisk360 Phase 1 Project Scope

> Historical scope: this document records the Phase 1 foundation. Dashboards, reporting,
> evidence, and remediation have since been implemented. See the [current README](../README.md)
> for present capabilities and limitations.

## Purpose

CyberRisk360 is a cybersecurity governance, risk, and compliance (GRC) reference application. Its purpose is to demonstrate how an organization can document important technology assets, identify cybersecurity risks, score those risks consistently, and communicate risk information to people with different responsibilities.

## Fictional organization

EagleShield Community Bank is a fictional community bank with approximately 50 employees. It provides online and mobile banking services and handles customer financial and identity information. Its technology environment includes Microsoft 365, employee laptops, an AWS-hosted customer portal, a third-party payment processor, branch-office networking equipment, and internal file storage and backups.

EagleShield Community Bank and all names, assets, risks, owners, departments, controls, dates, and other data in CyberRisk360 are entirely fictional. Nothing in this project represents a real organization, person, system, incident, or assessment.

## Included in the first version

Phase 1 includes the project design and a small fictional sample data set:

- A defined project scope for the initial version.
- A data dictionary for every field in the asset and risk samples.
- A simple five-level likelihood and impact methodology.
- Inherent and residual risk calculations with rating thresholds.
- Eight representative banking technology assets.
- Ten representative cybersecurity risks linked to those assets.
- Risk ownership, treatments, status, target dates, existing controls, and NIST Cybersecurity Framework (CSF) function labels.
- Validation of IDs, relationships, risk calculations, ratings, dates, and CSV structure.

## Excluded from the first version

Phase 1 does not include:

- A production application, database, dashboard, or reporting interface.
- Authentication, authorization, user accounts, or role-based access control.
- Integrations with Microsoft 365, AWS, payment processors, scanners, ticketing systems, or other live services.
- Automated evidence collection, continuous monitoring, control testing, vulnerability scanning, or incident response automation.
- A complete asset inventory, enterprise risk register, regulatory assessment, audit, or compliance certification.
- Real customer, employee, vendor, financial, security, or operational data.
- Advanced application features or deployment to a production environment.

## Expected users

- **GRC analyst:** Maintains asset and risk records, applies the methodology, and supports reporting.
- **Security manager:** Reviews cybersecurity exposure, control performance, and treatment priorities.
- **Control owner:** Operates and improves assigned safeguards and provides control-status information.
- **Risk owner:** Accepts accountability for a risk and coordinates its treatment and target date.
- **Executive:** Uses summarized risk information to make prioritization, funding, and risk-acceptance decisions.

## Expected outcome

The expected outcome is a clear, internally consistent foundation for later CyberRisk360 phases. A beginner should be able to understand what is in scope, interpret each data field, follow the risk-scoring calculations, and use the sample files as a starting point for future application, reporting, or governance work. The sample scores support prioritization and discussion; they are not a real assessment of any bank.
