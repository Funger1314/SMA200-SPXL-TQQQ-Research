#!/usr/bin/env bash
# One entry point: tests -> all analyses -> tables -> manuscript -> result check.
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest -q
python scripts/v4_run.py
python scripts/v4_tables.py
python paper/build_v4.py
python scripts/verify_results.py
