# 5. Multi-Factor Risk Scoring Formula

- **Status**: Accepted
- **Date**: 2026-07-20
- **Deciders**: Security & Reliability Team

## Context & Problem Statement

Issue tracking systems often classify issue severity solely based on static log levels (`ERROR`, `WARNING`). This fails to account for architectural business impact, vulnerability likelihood, or high-volume recurring incidents.

## Decision Drivers

- Objective 0.0 to 10.0 risk scoring system.
- Balanced incorporation of static baseline risk (Impact & Likelihood) and dynamic incident volume (Frequency).
- Automatic categorization into actionable severity tiers (`CRI`, `MED`, `LOW`).

## Decision Outcome

**Chosen Option**: **Multi-Factor Risk Scoring Formula**.

$$\text{Risk Score} = \min\left(10.0, (\text{Base Impact} \times \text{Base Likelihood}) + \min(3.0, \text{Frequency} \times 0.1)\right)$$

- **Severity Tiers**:
  - `Risk Score >= 8.0` $\rightarrow$ **CRI** (Critical)
  - `Risk Score >= 5.0` $\rightarrow$ **MED** (Medium)
  - `Risk Score < 5.0` $\rightarrow$ **LOW** (Low)

## Consequences

- **Positive**: Provides prioritizable risk scores; prevents high-volume low-severity logs from over-escalating while elevating true systemic vulnerabilities.
- **Negative**: Requires maintainers to specify baseline impact/likelihood parameters when introducing new diagnostic detection rules (`RULE_DEFINITIONS`).
