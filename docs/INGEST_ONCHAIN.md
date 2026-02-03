# On-chain Ingestion

## What it does
Scans proxy contracts for upgrade-related events:
- `Upgraded(address)`
- `AdminChanged(address,address)`
- `BeaconUpgraded(address)`

## Requirements
- `RPC_URL` in `.env` or environment.
- `WATCHLIST_PATH` pointing to proxy addresses.

## Run
- `pip install -r requirements.txt`
- `python scripts/ingest_onchain.py`

Output is written to `data/ingest/upgrade_events.jsonl`.

## Block range
- Default: last `LOOKBACK_BLOCKS` blocks (default 1).
- Override with `START_BLOCK` / `END_BLOCK`.
  
Note: Some free-tier RPCs limit the maximum log range per request, so keep
`LOOKBACK_BLOCKS` small unless your provider allows larger ranges.
