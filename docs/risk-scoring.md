# Risk Scoring & Severity Model

## 1. Overview

The **Risk Scoring Engine** evaluates detected system issues and assigns a quantitative risk score ranging from **0.0 to 10.0**. This score determines the issue's severity category, helping engineering teams prioritize critical security and infrastructure vulnerabilities.

## 2. Risk Scoring Formula

The calculation combines baseline architectural severity (Impact & Likelihood) with real-time incident frequency:

$$\text{Risk Score} = \min\left(10.0, \max\left(0.0, (\text{Base Impact} \times \text{Base Likelihood}) + \text{Frequency Factor}\right)\right)$$

Where:
$$\text{Frequency Factor} = \min(3.0, \text{Frequency} \times 0.1)$$

### Parameter Definitions
- **Base Impact (1.0 to 5.0)**: Represents potential business, financial, or data loss severity if unmitigated.
- **Base Likelihood (0.0 to 1.0)**: Estimated probability of recurring occurrence based on system conditions.
- **Frequency**: The total count of raw matching logs grouped under the issue cluster.
- **Frequency Factor Cap**: Capped at **3.0** to prevent high-volume low-impact logs from distorting baseline severity beyond realistic limits.

---

## 3. Severity Threshold Classification

Scores mapped to standardized severity levels:

| Risk Score Range | Severity Code | Severity Label | Description |
| :--- | :--- | :--- | :--- |
| **8.0 - 10.0** | **CRI** | Critical | High business impact; requires immediate developer intervention. |
| **5.0 - 7.99** | **MED** | Medium | Moderate impact or high frequency; should be resolved in current sprint. |
| **0.0 - 4.99** | **LOW** | Low | Minor operational anomaly or telemetry warning. |

---

## 4. Rule Categories (`RULE_DEFINITIONS`)

Issue detection rules map log keywords to specific operational categories:

| Category Code | Category Name | Sample Scenario | Base Impact | Base Likelihood |
| :--- | :--- | :--- | :--- | :--- |
| **DI** | Data Integrity | Duplicate request ingestion, unique key constraint failure | 4.5 | 0.85 |
| **CON** | Concurrency | Database transaction deadlock, concurrent webhook clash | 4.8 | 0.80 |
| **FH** | Failure Handling | External API outage, un-retried failed job, cascading timeout | 4.6 | 0.88 |
| **OBS** | Observability | Missing distributed trace correlation ID, unstructured logs | 3.0 | 0.95 |
| **SEC** | Security | Repeated unauthorized access, admin route probing | 5.0 | 0.85 |

---

## 5. Issue ID Naming Standard

Detected issues receive standard identifier strings:

$$\text{Format: } [\text{SEVERITY}]-[\text{CATEGORY}]-[\text{SERIAL}]$$

Examples:
- `CRI-DI-001`: Critical Data Integrity issue #1
- `MED-CON-002`: Medium Concurrency issue #2
- `LOW-OBS-001`: Low Observability issue #1
