# CyberRisk360 demo walkthrough

Follow one phishing scenario from its affected asset to the control, supporting evidence, and remediation action. This tour uses the included synthetic records for the fictional EagleShield Community Bank.

You can [read an actual generated executive report](examples/executive-report.md) on GitHub without installing anything. To explore the interface, follow the [quick start](../README.md#quick-start), then use the sidebar **Navigation** menu to switch pages.

## Five-minute tour

Keep filters at **All** unless specified below. Use **Reset Filters** on a page if earlier searches hide a record. Relationships are shown in tables; use Navigation to open the next register.

1. **Start with the risk.** Open **Risk Register** and enter `RSK-001` in **Search risks**. “Employee phishing compromise” affects `AST-003`. Likelihood 4 × impact 4 gives an inherent score of **16 (High)**. The recorded risk-level control-effectiveness estimate of 60% gives a residual score of **6.40 (Low)**. Its treatment is Mitigate and status is In Progress.

2. **Inspect the affected asset.** Open **Asset Inventory**, enter `AST-003` in **Search assets**, and choose `AST-003` under **Select an asset**. The Microsoft 365 record describes fictional email, collaboration, and productivity services. **Risks Affecting This Asset** includes `RSK-001`; **Controls Mapped to This Asset** includes `CTL-002`.

3. **Trace the control's supporting records.** Open **Security Controls**, enter `CTL-002` in **Search controls**, and choose `CTL-002` under **Select a control**. “Email security filtering” is Implemented, uses the Protect function label, and maps to `AST-003` and `RSK-001`. **Linked Evidence** shows `EVD-002`; **Linked Remediation Actions** shows `ACT-001`. Its control-level effectiveness of **78.50%** is a separate estimate from the risk's combined 60%; the application does not automatically aggregate mapped control values into risk scores.

4. **Review evidence freshness.** Open **Control Evidence** and enter `EVD-002` in **Search evidence**. The “Email filtering effectiveness report” expires on **2026-09-01**. Its stored Status is **Expiring Soon**, while the calculated Evidence Condition is **Expiring Within 30 Days**. The storage reference describes where a fictional artifact would reside; CyberRisk360 stores evidence metadata, not the report file itself.

5. **Review the follow-up action.** Open **Remediation Actions** and enter `ACT-001` in **Search actions**. “Expand phishing simulations” links to both `RSK-001` and `CTL-002`. It is High priority, In Progress, 60% complete, and assigned to the Security Awareness Manager. Its due date of **2026-07-31** makes the displayed Overdue value **Yes**.

6. **Take the findings into a report.** Open **Reports & Exports** and expand **Preview Executive Report**. In **Download Center**, choose **Download Executive Report** for Markdown or **Download Complete Report Package** for a ZIP containing the report, all five CSV registers, and a text manifest. The report includes evidence priorities and `ACT-001` among overdue actions. See the [checked-in example](examples/executive-report.md) and [reporting/export documentation](reporting_exports_workflow.md) for the output and calculation details.

## How to interpret the demo

The interface and default reports calculate evidence expiration and overdue actions against **2026-08-05**, a fixed reference date that keeps the demo reproducible. These are not today's live operational indicators. Stored evidence status and the calculated expiration condition remain separate.

An action is overdue when its due date is before the reference date and its status is neither Closed nor Cancelled. Completed actions can therefore still appear as overdue; the report's total of four should not be read as four unfinished actions.

Risk scores use a simplified prioritization model. NIST CSF labels group records by function, and coverage percentages measure the presence of linked records. Neither constitutes a control-effectiveness assessment or a compliance conclusion. See the [risk methodology](risk_methodology.md) and [project scope](project_scope.md).

For technical validation, open **System Status** to inspect the sample-data integrity and project-health checks. These checks assess dataset consistency and application readiness, not security certification.

## About the example report

[examples/executive-report.md](examples/executive-report.md) is generated directly by `export_manager.generate_management_report_markdown`, using `project_health.load_all_project_data()` and the reporting engine's `REFERENCE_DATE`. It is a snapshot of the bundled data and contains no manually substituted results. Regenerate it when the sample data or report generator changes.
