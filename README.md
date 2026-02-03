# proxywatch

ProxyWatch monitors smart contract upgrades (EIP-1967/ProxyAdmin) and produces
clear, auditable upgrade reports for DeFi teams and DAOs.

## MVP scope
- Track proxy upgrade events: `Upgraded`, `AdminChanged`, `BeaconUpgraded`.
- Normalize into a canonical upgrade event schema.
- Maintain an upgrade history ledger per proxy.
- Generate a human-friendly report (Markdown) per upgrade.
- Provide a read-only API + CLI for lookup.

## Why it matters
- Upgrade transparency reduces operational and governance risk.
- Helps auditors and community members verify what actually changed.
- Demonstrates Web3 + data pipeline + security workflow skills.

## Architecture (high level)
Watchlist -> On-chain logs -> Normalize -> Store -> Diff -> Reports -> API/CLI

See docs/ARCHITECTURE.md for more detail.

## Planned repository layout
- src/ingest/        On-chain log ingestion
- src/normalize/     Canonical event schema + validators
- src/diff/          Bytecode + selector diffs
- src/report/        Report generation (Markdown/JSON)
- src/api/           Read-only API
- src/cli/           CLI tools
- tests/             Unit + integration tests
- docs/              Design docs and roadmap

## Tech stack (initial)
- Python, Web3.py
- Storage: DuckDB + Parquet
- API: FastAPI
- Optional: LLM summary for upgrade rationale

## Phase 0: schema + fixtures + validator
- Fixtures live in `data/fixtures/*.jsonl`.
- Schema is defined in `src/normalize/schema.py`.
- Validate fixtures:
  - `pip install -r requirements.txt`
  - `python scripts/validate_fixtures.py`

## Phase 1: on-chain ingestion
- Scan watchlisted proxies for upgrade events.
- Details: `docs/INGEST_ONCHAIN.md`.
- Run:
  - `pip install -r requirements.txt`
  - `python scripts/ingest_onchain.py`
- Output: `data/ingest/upgrade_events.jsonl`

## Phase 2: diff engine + report generator
- Compare implementation bytecode + selectors across upgrades.
- Details: `docs/REPORTS.md`.
- Run:
  - `pip install -r requirements.txt`
  - `python scripts/generate_reports.py`
- Output: `data/reports/*.json` and `data/reports/*.md`

## Roadmap
- Phase 0: schema + fixtures
- Phase 1: on-chain ingestion + watchlist
- Phase 2: diff engine + report generator
- Phase 3: API + CLI
