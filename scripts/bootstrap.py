# LEGACY (v1) - kept for the audit trail only. NOT used by the current (v4) pipeline.
# Current entry point: ./run_all.sh  (scripts/v4_run.py, scripts/engine.py, scripts/data_checks.py)
"""Primary v2 risk-inference entrypoint (monthly legacy evidence only)."""
from reviewer_risk_bootstrap import evaluate
if __name__=='__main__':
    print(evaluate().to_string(index=False))
