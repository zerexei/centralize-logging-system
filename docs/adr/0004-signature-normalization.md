# 4. Regex Log Message Signature Normalization

- **Status**: Accepted
- **Date**: 2026-07-20
- **Deciders**: Data & Analytics Team

## Context & Problem Statement

High-volume log streams contain identical error patterns with variable arguments (IPs, numbers, UUIDs, IDs). Aggregating raw log strings directly creates duplicate issue entries and obscures systemic problem areas.

## Decision Drivers

- Fast, deterministic grouping of raw log messages.
- Automatic extraction of variable telemetry data.
- Stable, repeatable fingerprint generation for tracking issues over time.

## Decision Outcome

**Chosen Option**: **Regex Parameter Abstraction**.

- Applies regex substitutions:
  - `re.sub(r'\d+', 'X', msg)`
  - `re.sub(r'[0-9a-fA-F]{8}-...', 'UUID', msg)`
- Groups logs by composite key `(service, level, environment, normalized_message)`.
- Hashes group keys with MD5 to produce stable issue identifiers (`iss_<hash>`).

## Consequences

- **Positive**: Reduces log noise by up to 95%; groups thousands of raw log entries into clean issue clusters.
- **Negative**: Extremely complex or unstructured log formats may produce broad group signatures if messages lack standard parameter boundaries.
