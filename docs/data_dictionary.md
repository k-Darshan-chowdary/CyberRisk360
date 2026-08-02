# CyberRisk360 Data Dictionary

This dictionary documents every column used by the Phase 1 asset and risk CSV files. All examples are fictional. “Required” means the field must contain a value in every sample record.

## Asset fields (`data/sample_assets.csv`)

| Field name | Description | Data type | Example | Required |
|---|---|---|---|---|
| `asset_id` | Unique identifier for an asset, using the `AST-###` format. | String | `AST-001` | Yes |
| `asset_name` | Short, human-readable name of the asset. | String | `Customer Records Database` | Yes |
| `asset_type` | General technology or service category. | String | `Database` | Yes |
| `asset_owner` | Fictional role accountable for the asset. | String | `Director of Information Technology` | Yes |
| `department` | Business department primarily responsible for or dependent on the asset. | String | `Information Technology` | Yes |
| `data_classification` | Sensitivity category of the data stored, processed, or accessed by the asset. | Enum string: `Public`, `Internal`, `Confidential`, or `Restricted` | `Restricted` | Yes |
| `business_criticality` | Importance of the asset to business operations. | Enum string: `Low`, `Medium`, `High`, or `Critical` | `Critical` | Yes |
| `location` | Fictional physical, cloud, or service location of the asset. | String | `AWS us-east-2` | Yes |
| `description` | Brief explanation of the asset and its business purpose. | String | `Stores fictional customer profile and account data.` | Yes |

## Risk fields (`data/sample_risks.csv`)

| Field name | Description | Data type | Example | Required |
|---|---|---|---|---|
| `risk_id` | Unique identifier for a risk, using the `RSK-###` format. | String | `RSK-001` | Yes |
| `risk_title` | Short, human-readable name of the risk scenario. | String | `Employee phishing compromise` | Yes |
| `threat` | Actor, event, or condition that could cause harm. | String | `Phishing attacker` | Yes |
| `vulnerability` | Weakness or exposure that the threat could exploit. | String | `Users may open deceptive messages` | Yes |
| `affected_asset_id` | Foreign-key reference to an existing `asset_id` in `sample_assets.csv`. | String | `AST-003` | Yes |
| `likelihood` | Estimated probability level before considering existing controls. | Integer from 1 through 5 | `4` | Yes |
| `impact` | Estimated consequence level before considering existing controls. | Integer from 1 through 5 | `4` | Yes |
| `inherent_score` | Risk score before existing controls, calculated as likelihood multiplied by impact. | Integer from 1 through 25 | `16` | Yes |
| `inherent_rating` | Rating assigned to the inherent score using the defined thresholds. | Enum string: `Low`, `Medium`, `High`, or `Critical` | `High` | Yes |
| `existing_controls` | Concise description of safeguards currently reducing the risk. | String | `Email filtering; MFA; awareness training` | Yes |
| `control_effectiveness_pct` | Estimated combined effectiveness of existing controls, expressed as a whole-number percentage. | Integer from 0 through 100 | `60` | Yes |
| `residual_score` | Risk remaining after controls, calculated with the residual-risk formula and rounded to two decimal places. | Decimal from 0.00 through 25.00 | `6.40` | Yes |
| `residual_rating` | Rating assigned to the residual score using the same score thresholds. | Enum string: `Low`, `Medium`, `High`, or `Critical` | `Low` | Yes |
| `risk_owner` | Fictional role accountable for monitoring and treating the risk. | String | `Information Security Manager` | Yes |
| `treatment` | Selected response to the risk. | Enum string: `Mitigate`, `Avoid`, `Transfer`, or `Accept` | `Mitigate` | Yes |
| `status` | Current state of the risk or its treatment activity. | Enum string: `Open`, `In Progress`, `Monitoring`, or `Accepted` | `In Progress` | Yes |
| `target_date` | Planned date for completing or reviewing the treatment, in ISO format. | Date (`YYYY-MM-DD`) | `2026-10-31` | Yes |
| `nist_csf_function` | Primary NIST CSF function associated with the risk or planned treatment. | Enum string: `Govern`, `Identify`, `Protect`, `Detect`, `Respond`, or `Recover` | `Protect` | Yes |
