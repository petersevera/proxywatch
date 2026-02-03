# Reports

ProxyWatch can generate deterministic upgrade reports from ingested events.

## Inputs
- `data/ingest/upgrade_events.jsonl` (from `scripts/ingest_onchain.py`)
- `RPC_URL` for fetching implementation bytecode

## Run
- `pip install -r requirements.txt`
- `python scripts/generate_reports.py`

Reports are written to `data/reports/` as both `.json` and `.md` per upgrade event.

## What gets compared
- Bytecode hash + size
- Function selectors (extracted via PUSH4 scanning)

## Config (optional)
- `INGEST_PATH` - override ingest file path
- `REPORT_DIR` - output directory
- `BYTECODE_CACHE` - local cache of fetched bytecode
- `MAX_SELECTOR_LIST` - max selector entries to show in Markdown

Note: Free-tier RPC providers may rate-limit calls. The generator caches bytecode
per implementation address to minimize requests.
