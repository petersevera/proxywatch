# API

ProxyWatch exposes a read-only FastAPI service for upgrade data and reports.

## Run
- `pip install -r requirements.txt`
- `python scripts/run_api.py`

Default: `http://127.0.0.1:8000`

## Endpoints
- `GET /health` -> basic liveness
- `GET /proxies` -> list unique proxy addresses
- `GET /events` -> list events
  - Query: `proxy_address`, `event_type`, `chain`, `limit`, `offset`
- `GET /reports` -> list reports
  - Query: `proxy_address`, `limit`, `offset`
- `GET /reports/{event_id}` -> single report JSON

## Config (optional)
- `INGEST_PATH` - upgrade events JSONL path
- `REPORT_DIR` - report output directory
- `API_HOST` - bind host (default 127.0.0.1)
- `API_PORT` - bind port (default 8000)
- `API_RELOAD` - enable reload (true/false)
