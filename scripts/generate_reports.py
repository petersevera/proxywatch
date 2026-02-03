#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from web3 import Web3

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from diff.bytecode import (
    BytecodeSummary,
    fetch_bytecode,
    load_bytecode_cache,
    save_bytecode_cache,
    summarize_bytecode,
)
from diff.selectors import diff_selectors
from normalize.schema import UpgradeEvent
from report.report import build_report
from report.render import render_markdown


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


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_events(path: Path) -> List[UpgradeEvent]:
    events: List[UpgradeEvent] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(UpgradeEvent.model_validate_json(line))
    return events


def _event_sort_key(event: UpgradeEvent) -> tuple:
    block_number = event.block_number if event.block_number is not None else -1
    log_index = event.log_index if event.log_index is not None else -1
    return (event.proxy_address, block_number, log_index)


def main() -> int:
    env_file = _load_env_file(Path(".env"))
    rpc_url = _env_value("RPC_URL", env_file)
    if not rpc_url:
        print("RPC_URL is required", file=sys.stderr)
        return 1

    ingest_path = Path(
        _env_value("INGEST_PATH", env_file, "data/ingest/upgrade_events.jsonl")
    )
    report_dir = Path(_env_value("REPORT_DIR", env_file, "data/reports"))
    cache_path = Path(_env_value("BYTECODE_CACHE", env_file, "data/cache/bytecode.json"))
    max_selectors = _parse_int(_env_value("MAX_SELECTOR_LIST", env_file), 20)

    events = _load_events(ingest_path)
    upgraded_events = [event for event in events if event.event_type == "upgraded"]
    if not upgraded_events:
        print(f"No upgraded events found in {ingest_path}")
        return 0

    upgraded_events.sort(key=_event_sort_key)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("RPC connection failed", file=sys.stderr)
        return 1

    cache = load_bytecode_cache(cache_path)

    implementation_addresses = {
        event.implementation_address
        for event in upgraded_events
        if event.implementation_address
    }

    summaries: Dict[str, BytecodeSummary] = {}
    for address in sorted(implementation_addresses):
        if not address:
            continue
        bytecode_hex = fetch_bytecode(w3, address, cache)
        summaries[address] = summarize_bytecode(bytecode_hex)

    save_bytecode_cache(cache_path, cache)

    report_dir.mkdir(parents=True, exist_ok=True)

    last_impl_by_proxy: Dict[str, Optional[str]] = {}

    for event in upgraded_events:
        previous_impl = last_impl_by_proxy.get(event.proxy_address)
        current_impl = event.implementation_address or ""
        current_summary = summaries.get(current_impl)
        if current_summary is None:
            current_summary = summarize_bytecode("0x")
        previous_summary = summaries.get(previous_impl) if previous_impl else None

        selector_diff = diff_selectors(
            previous_summary.selectors if previous_summary else set(),
            current_summary.selectors,
        )

        report = build_report(
            event=event,
            previous_impl=previous_impl,
            previous_summary=previous_summary,
            current_summary=current_summary,
            selector_diff=selector_diff,
        )

        report_json_path = report_dir / f"{event.event_id}.json"
        report_md_path = report_dir / f"{event.event_id}.md"

        report_json_path.write_text(
            json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        report_md_path.write_text(
            render_markdown(report.as_dict(), max_selectors=max_selectors),
            encoding="utf-8",
        )

        last_impl_by_proxy[event.proxy_address] = event.implementation_address

    print(f"wrote {len(upgraded_events)} reports to {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
