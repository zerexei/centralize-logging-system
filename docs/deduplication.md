# Log Deduplication & Signature Normalization

## 1. Executive Summary

Log streams from microservices frequently contain repeated error signatures that differ only in dynamic parameters (e.g. timestamps, transaction IDs, user IDs, numbers). To prevent noise and aggregate related events into distinct actionable items, the system applies **Regex Signature Normalization** and **Fingerprint Grouping**.

## 2. Signature Normalization Algorithm

Log signature normalization is implemented in `LogService.get_issues()` and `IssueService.detect_issues()`:

```python
def normalize_msg(msg: str) -> str:
    if not msg:
        return "Empty log message"
    # Replace numeric strings/IDs with generic placeholder 'X'
    msg = re.sub(r'\d+', 'X', msg)
    # Replace UUID structures with generic placeholder 'UUID'
    msg = re.sub(
        r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        'UUID',
        msg
    )
    return msg.strip()
```

### Examples of Signature Normalization

| Raw Input Log Message | Normalized Message Signature |
| :--- | :--- |
| `Failed to connect to DB host 10.0.4.12 on port 5432` | `Failed to connect to DB host X.X.X.X on port X` |
| `User 88192 updated payment key e4b2d184-7a31-4c12-9b21-123456789abc` | `User X updated payment key UUID` |
| `HTTP 500 timeout after 3000ms` | `HTTP X timeout after Xms` |

---

## 3. Grouping & Deduplication Logic

Raw logs are aggregated into issue buckets using a composite key:

$$\text{Group Key} = \text{service} + \text{":"} + \text{level} + \text{":"} + \text{environment} + \text{":"} + \text{normalized\_msg}$$

### Issue Fingerprint Hash

Each unique group key is hashed using MD5 to generate a stable, deterministic issue identifier (`id`):

```python
issue_id_hash = hashlib.md5(key.encode()).hexdigest()
issue_id = f"iss_{issue_id_hash[:12]}"
```

### Group Metadata Aggregation

During log scanning, the deduplication engine updates summary metrics for each issue cluster:
- **`count`**: Total number of matching raw log occurrences.
- **`first_seen`**: ISO 8601 timestamp of earliest occurrence.
- **`last_seen`**: ISO 8601 timestamp of most recent occurrence.
- **`status`**: Marked as `Active` if level is `ERROR` or `CRITICAL`; otherwise `Monitored`.
