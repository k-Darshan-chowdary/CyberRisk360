# Public launch checklist

This checklist covers a public release of the existing synthetic-data GRC demo.
It does not declare production readiness or confirm that a hosted instance exists.

## Repository discoverability

Use the following copy in the repository's **About** editor. These are GitHub
settings, not values that GitHub automatically imports from this document.

**Description**

> Cybersecurity GRC reference app for asset inventory, risk scoring, control mapping, evidence tracking, remediation, and executive reporting. Python + Streamlit; read-only synthetic-data demo.

**Topics**

```text
cybersecurity
grc
risk-management
governance-risk-compliance
nist-csf
python
streamlit
security-controls
risk-assessment
```

**Website:** leave empty until there is a verified demo or documentation site.
After deploying and checking an instance, add the same URL to About and the README.
Do not use a guessed Streamlit URL or a badge that implies an unavailable demo.

## Before a public announcement

- [x] Select and commit a license. CyberRisk360 uses the [MIT License](../LICENSE),
  linked from the README with a matching badge.
- [ ] Merge the reviewed launch documentation and contributor files with passing CI.
- [ ] Check the About description and topics against the current capabilities.
- [ ] Run all [quality gates](../CONTRIBUTING.md#validate-a-change) from a clean
  Python 3.13 environment and record the commit and results in the release notes.
- [ ] Follow the [demo walkthrough](DEMO.md), inspect all nine pages, and verify
  the seven download controls in Reports & Exports.
- [ ] Confirm the sample-data integrity check still passes after the walkthrough.
- [ ] Verify a usable private vulnerability-reporting route from the Security tab
  and update [SECURITY.md](../SECURITY.md) if the route changes.
- [ ] Review the README's visuals and [example executive report](examples/executive-report.md)
  against the current app. Keep the synthetic-data label and reference date visible.
- [ ] If hosting a demo, complete [DEPLOYMENT.md](../DEPLOYMENT.md), exercise the
  deployed pages and downloads, and then publish the verified URL.
- [ ] Create a release from the tested commit with the current feature list,
  setup instructions, limitations, and known issues. Avoid invented user counts,
  certifications, endorsements, or release dates.

## Release notes outline

Use this outline when an actual release is ready. Replace each field with facts
from that release; the outline itself is not a release announcement.

```markdown
## CyberRisk360 <version>

CyberRisk360 connects asset inventory, risk assessment, controls, evidence
metadata, remediation, and executive reporting in a read-only GRC application.

### Included
- <Verified changes in this release>

### Try it
- <README quick-start link>
- <Demo walkthrough link>
- <Verified hosted URL, if available>

### Validation
- Commit: <full commit SHA>
- Python: <tested version>
- Tests, integrity, and health: <actual results>

### Scope
Synthetic data only. Fixed demonstration reference date: 2026-08-05.
No authentication, live integrations, or production-data support.
NIST CSF function labels are not proof of compliance.

### License and contribution
- <Committed license link>
- <Contributor guide and issue tracker links>
```

## After launch

Share the concrete GRC workflow and a reproducible example with relevant
communities, following each community's posting rules. Keep feedback in the issue
tracker and turn reproducible problems into focused changes.

Use **Insights → Traffic** to assess repository views, visitors, clones, and
referrers. Watchers are notification subscribers, not a view count. Compare those
signals with actionable feedback; repository polish alone does not guarantee reach.
See [GitHub's traffic documentation](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository).
