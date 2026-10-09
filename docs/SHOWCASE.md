# CyberRisk360 project showcase

Built by [Darshan Konjeti](https://github.com/k-Darshan-chowdary).

CyberRisk360 makes a GRC workflow inspectable: start with an asset and risk,
review the safeguards and evidence, identify follow-up work, then generate an
executive report. The example organization, EagleShield Community Bank, and all
records are fictional.

## What the project demonstrates

| Engineering work | Evidence to inspect |
| --- | --- |
| Explainable risk calculations with validated inputs | [Risk engine](../risk_engine.py), [methodology](risk_methodology.md), and [tests](../tests/test_risk_engine.py) |
| Five related registers with validation and reference checks | [Data dictionary](data_dictionary.md) and [project health](../project_health.py) |
| An interactive investigation and isolated what-if calculator | [Risk explorer](../ui/risk_page.py) and [visitor-journey tests](../tests/test_risk_explorer.py) |
| Management reporting and in-memory CSV/ZIP generation | [Export manager](../export_manager.py) and [generated report](examples/executive-report.md) |
| Reproducible synthetic-data evaluation | [Integrity guard](../integrity_guard.py), [sample manifest](../data/integrity_manifest.json), and [CI](../.github/workflows/ci.yml) |

The scenario has 8 assets, 10 risks, 12 controls, 12 evidence records, and 10
remediation actions. Nine Streamlit pages expose the workflow. The risk-level
effectiveness estimate is separate from individual control effectiveness and
evidence freshness. NIST CSF function labels organize the records; they do not
establish compliance.

## A 45-second demo script

1. **0–10 seconds — The problem.** Show the Executive Dashboard: “A risk score
   alone doesn't explain what needs attention. I built CyberRisk360 to connect
   that score to assets, safeguards, evidence, and follow-up work.”
2. **10–25 seconds — The workflow.** Choose **Explore the phishing scenario**.
   Show `RSK-001`, its Microsoft 365 asset, mapped controls, supporting evidence,
   and `ACT-001`. Explain the synthetic data and fixed date, 2026-08-05.
3. **25–35 seconds — The reasoning.** Set scenario effectiveness from 60% to 0%:
   residual risk changes from 6.40 (Low) to 16.00 (High). Explain that the
   calculator is hypothetical and the recorded assessment stays unchanged.
4. **35–45 seconds — The output.** Choose **Continue to executive reports**.
   Show the Markdown preview and ZIP download, then end on the repository URL.

Use the running app for a screen recording. Keep the synthetic-data label
visible and include captions so viewers can follow without audio.

## Announcement draft

Adapt this after the changes are merged and the linked default branch is current.
This is draft copy; it has not been posted to any social account or community.

> I built CyberRisk360, a Python + Streamlit project that connects cybersecurity
> risk assessment to controls, evidence, remediation, and executive reporting.
>
> One example: an employee phishing scenario starts at 16 (High). With a 60%
> assessed control-effectiveness estimate, residual risk is 6.40 (Low). You can
> inspect the linked asset, safeguards, evidence, and follow-up actions, then
> change the assumptions in a what-if calculator.
>
> The app uses a fictional bank and synthetic data. It includes validated
> registers, in-memory report exports, integrity checks, and automated tests.
>
> Code, screenshots, setup, and an example executive report:
> https://github.com/k-Darshan-chowdary/CyberRisk360
>
> I'd welcome feedback from GRC and security practitioners: which part of a
> risk-to-remediation workflow would you want explained more clearly? If it's
> useful, star it or fork it to explore your own fictional scenario.

## Help someone make their first contribution

These are suggested tasks, not claims that issues or features already exist:

- Walk through the app using only a keyboard and report the exact step where
  navigation or a chart becomes difficult, with reproduction steps.
- Add a worked scoring example around a rating threshold, checking the math
  against `assess_risk` and explaining the limitation of the model.
- Propose a fictional scenario for a different industry, including valid
  register relationships and an explanation of the business impact.

Start with [CONTRIBUTING.md](../CONTRIBUTING.md). Discuss schema, scoring, or
sample-data changes before implementing them. Keep real organization data out.

## Publishing and measuring reach

- Merge a reviewed change after CI passes, then publish a release tied to the
  tested commit with its actual changes and validation results.
- Deploy and verify the synthetic demo using [DEPLOYMENT.md](../DEPLOYMENT.md),
  then add its verified URL to the README and repository About section. No live
  demo is claimed by this document.
- Pin the repository on your profile. Share the short recording and a concrete
  lesson in communities where project showcases are welcome, following their
  posting rules. Tailor the explanation to the audience.
- Compare [GitHub traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository),
  clones, referrers, stars, forks, and actionable feedback after sharing. Repository
  improvements can reduce friction, but do not guarantee views or engagement.
