from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastapi import FastAPI, HTTPException, Query

from normalize.schema import UpgradeEvent

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key) or env_file.get(key, default)


def _resolve_path(value: Optional[str], fallback: Path) -> Path:
    if not value:
        return fallback
    return Path(value)


def _load_events(path: Path) -> List[UpgradeEvent]:
    events: List[UpgradeEvent] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(UpgradeEvent.model_validate_json(line))
        except Exception:
            continue
    return events


def _event_sort_key(event: UpgradeEvent) -> tuple:
    block_number = event.block_number if event.block_number is not None else -1
    log_index = event.log_index if event.log_index is not None else -1
    return (event.event_time, block_number, log_index)


def _filter_events(
    events: Iterable[UpgradeEvent],
    proxy_address: Optional[str],
    event_type: Optional[str],
    chain: Optional[str],
) -> List[UpgradeEvent]:
    filtered = []
    for event in events:
        if proxy_address and event.proxy_address.lower() != proxy_address.lower():
            continue
        if event_type and event.event_type != event_type:
            continue
        if chain and event.chain != chain:
            continue
        filtered.append(event)
    return filtered


def _load_report(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_report_path(report_dir: Path, event_id: str) -> Path:
    if "/" in event_id or ".." in event_id:
        raise HTTPException(status_code=400, detail="invalid event_id")
    return report_dir / f"{event_id}.json"


def create_app() -> FastAPI:
    env_file = _load_env_file(REPO_ROOT / ".env")
    ingest_path = _resolve_path(
        _env_value("INGEST_PATH", env_file),
        REPO_ROOT / "data" / "ingest" / "upgrade_events.jsonl",
    )
    report_dir = _resolve_path(
        _env_value("REPORT_DIR", env_file),
        REPO_ROOT / "data" / "reports",
    )

    app = FastAPI(title="ProxyWatch API", version="0.1.0")
    app.state.ingest_path = ingest_path
    app.state.report_dir = report_dir

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/proxies")
    def list_proxies() -> Dict[str, List[str]]:
        events = _load_events(app.state.ingest_path)
        proxies = sorted({event.proxy_address for event in events})
        return {"proxies": proxies}

    @app.get("/events")
    def list_events(
        proxy_address: Optional[str] = None,
        event_type: Optional[str] = Query(default=None, pattern="^(upgraded|admin_changed|beacon_upgraded)$"),
        chain: Optional[str] = None,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> Dict[str, object]:
        events = _load_events(app.state.ingest_path)
        filtered = _filter_events(events, proxy_address, event_type, chain)
        filtered.sort(key=_event_sort_key)
        total = len(filtered)
        slice_events = filtered[offset : offset + limit]
        return {
            "total": total,
            "items": [event.model_dump(mode="json") for event in slice_events],
        }

    @app.get("/reports")
    def list_reports(
        proxy_address: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> Dict[str, object]:
        report_dir = app.state.report_dir
        if not report_dir.exists():
            return {"total": 0, "items": []}
        report_files = sorted(report_dir.glob("*.json"))
        reports: List[Dict[str, object]] = []
        for path in report_files:
            try:
                report = _load_report(path)
            except Exception:
                continue
            if proxy_address and str(report.get("proxy_address", "")).lower() != proxy_address.lower():
                continue
            reports.append(report)
        total = len(reports)
        sliced = reports[offset : offset + limit]
        return {"total": total, "items": sliced}

    @app.get("/reports/{event_id}")
    def get_report(event_id: str) -> Dict[str, object]:
        report_path = _safe_report_path(app.state.report_dir, event_id)
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="report not found")
        return _load_report(report_path)

    return app
