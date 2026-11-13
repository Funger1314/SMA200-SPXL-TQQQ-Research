# Scripts

| Status | File | Purpose |
|---|---|---|
| **current** | `engine.py` | data loading (strict validation), market construction, synthetic sleeve, simulator, metrics |
| **current** | `data_checks.py` | OHLCV validation, rule-based NYSE calendar |
| **current** | `rates.py` | lagged DTB3 T-bill proxy |
| **current** | `v4_run.py` | all v4 analyses → `data/v4_results`, `figures/v4` |
| **current** | `v4_tables.py` | manuscript tables → `paper/tables_v4` |
| **current** | `verify_results.py` | checks 312 headline values against `data/expected_results.json` |
| **current** | `fetch_yahoo.py` | re-download vendor files and record a download manifest |
| alias | `v3_engine.py` | re-exports `engine.py` (older imports) |
| historical v3 | `v3_run.py`, `v3_tables.py` | v3 analyses (`data/v3_results`) |
| historical v2 | `review_revision.py`, `reviewer_risk_bootstrap.py` | v2 engine (contains the exit-dust defect fixed in v3) |
| historical v1 | `reproduce.py`, `reproduce_legacy_v1.py`, `fetch_data.py`, `decode_ibkr_tail.py`, `decode_snapshot.py`, `build_snapshot_artifacts.py`, `bootstrap.py`, `bootstrap_legacy_v1.py` | mixed-archive + IBKR-tail pipeline |

Historical scripts carry a LEGACY banner and are kept only so the earlier drafts remain auditable.
