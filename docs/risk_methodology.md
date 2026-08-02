# CyberRisk360 Risk Methodology

## Purpose and use

This simplified methodology gives EagleShield Community Bank a consistent way to estimate and discuss fictional cybersecurity risks. Assessors select likelihood and impact levels, calculate inherent risk, estimate the effectiveness of current controls, and calculate residual risk. Scores support decision-making and do not replace professional judgment.

## Likelihood levels

Likelihood estimates how probable the scenario is before considering existing controls.

| Level | Label | Definition |
|---:|---|---|
| 1 | Rare | The scenario is highly unlikely and would be expected only in exceptional circumstances. |
| 2 | Unlikely | The scenario could occur, but it is not expected under normal conditions. |
| 3 | Possible | The scenario might occur and has a credible path to happening. |
| 4 | Likely | The scenario is expected to occur or has occurred in comparable organizations. |
| 5 | Almost certain | The scenario is expected frequently or is already occurring repeatedly. |

## Impact levels

Impact estimates the potential consequence if the scenario occurs, before considering existing controls.

| Level | Label | Definition |
|---:|---|---|
| 1 | Insignificant | Minimal operational disruption, negligible cost, and no meaningful data or compliance effect. |
| 2 | Minor | Limited disruption or cost that a team can resolve through routine procedures. |
| 3 | Moderate | Noticeable service disruption, financial loss, data exposure, or management attention. |
| 4 | Major | Serious customer, operational, financial, legal, regulatory, or reputational harm. |
| 5 | Severe | Prolonged or widespread harm that threatens critical services, customers, compliance, or organizational viability. |

## Inherent risk

Inherent risk is the estimated exposure before giving credit for existing controls. It combines the selected likelihood and impact levels:

```text
inherent_score = likelihood × impact
```

For example, likelihood 4 and impact 5 produce an inherent score of 20.

## Control effectiveness

`control_effectiveness_pct` estimates how much the current safeguards reduce the inherent exposure when considered together. It is recorded from 0 through 100 percent:

- `0%` means the controls provide no estimated reduction.
- `50%` means the controls reduce the inherent score by half.
- `100%` means the formula produces no remaining score; in practice, assessors should apply professional judgment before concluding that no risk remains.

The percentage is a simplified estimate based on control design, implementation, operation, coverage, and available evidence. It is not a control certification.

## Residual risk

Residual risk is the estimated exposure remaining after applying the effectiveness of existing controls:

```text
residual_score = inherent_score × (1 - control_effectiveness_pct / 100)
```

Residual scores are rounded to two decimal places. For example, an inherent score of 20 and control effectiveness of 45 percent produce a residual score of `20 × (1 - 45 / 100) = 11.00`.

## Risk ratings

The same rating thresholds apply to inherent and residual scores. Inherent scores are whole numbers; residual scores may contain decimals.

| Rating | Score range |
|---|---:|
| Critical | 20 through 25 (`20.00` to `25.00`) |
| High | 15 through 19 (at least `15.00` but below `20.00`) |
| Medium | 8 through 14 (at least `8.00` but below `15.00`) |
| Low | Below 8 (below `8.00`) |

## Risk treatments

- **Mitigate:** Reduce likelihood, impact, or both by implementing or improving controls.
- **Avoid:** Stop or change the activity that creates the risk so the scenario no longer applies.
- **Transfer:** Shift some financial or operational consequence to another party, such as through insurance or a contract, while recognizing that accountability may remain.
- **Accept:** Formally acknowledge the risk and retain it when it is within tolerance or additional treatment is not justified; acceptance should be authorized and reviewed.

## Judgment and review

Risk scoring creates a common starting point for prioritization, ownership, and treatment decisions. Scores support decision-making and do not replace professional judgment. Assumptions, control evidence, business context, regulatory obligations, threat changes, and risk tolerance should be considered, and scores should be reviewed when conditions change.
