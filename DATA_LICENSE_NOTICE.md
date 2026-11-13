# Data provenance and redistribution

1. **Current (v4) data.** The four files in `data/raw/` are Yahoo Finance daily bars exported with yfinance and obtained from the public repository github.com/hjyssg/tqqq_simulation. Yahoo's terms restrict redistribution, so these files are excluded from the public repository by `.gitignore`. They are supplied only in the private replication archive for reviewers. `scripts/fetch_yahoo.py` lets anyone re-download equivalent data and records a download manifest.
2. **Published outputs.** The repository contains code, derived statistics, figures and file hashes. It does not contain raw price files.
3. **Historical (v1/v2) data.** Earlier drafts used third-party GitHub archives plus a privately licensed Interactive Brokers tail. None of that data is used in v4, and none of it is distributed.
4. Do not commit raw vendor data, IBKR account data or API credentials to a public repository.

This is a publication-safety practice, not legal advice.
