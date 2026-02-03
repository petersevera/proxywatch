#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from web3 import Web3

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ingest.onchain import fetch_proxy_events


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_file: dict[str, str], default: str | None = None) -> str | None:
    return os.getenv(key) or env_file.get(key, default)


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_watchlist(path: Path) -> list[str]:
    if not path.exists():
        return []
    addresses = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        addresses.append(text)
    return addresses


def main() -> int:
    env_file = _load_env_file(Path(".env"))
    rpc_url = _env_value("RPC_URL", env_file)
    if not rpc_url:
        print("RPC_URL is required", file=sys.stderr)
        return 1

    chain = _env_value("CHAIN", env_file, "ethereum") or "ethereum"
    watchlist_path = Path(
        _env_value("WATCHLIST_PATH", env_file, "data/watchlist.txt")
    )
    lookback = _parse_int(_env_value("LOOKBACK_BLOCKS", env_file), 1)
    start_block = _parse_int(_env_value("START_BLOCK", env_file), -1)
    end_block = _parse_int(_env_value("END_BLOCK", env_file), -1)
    if lookback < 1:
        print("LOOKBACK_BLOCKS must be >= 1", file=sys.stderr)
        return 1

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("RPC connection failed", file=sys.stderr)
        return 1

    latest_block = w3.eth.block_number
    if end_block < 0:
        end_block = latest_block
    if start_block < 0:
        start_block = max(0, end_block - (lookback - 1))

    if start_block > end_block:
        print("START_BLOCK must be <= END_BLOCK", file=sys.stderr)
        return 1

    proxies = _load_watchlist(watchlist_path)
    if not proxies:
        print(f"No proxy addresses found in {watchlist_path}")
        return 1

    all_events = []
    for proxy in proxies:
        events = fetch_proxy_events(w3, proxy, start_block, end_block, chain)
        all_events.extend(events)

    output_dir = Path("data") / "ingest"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "upgrade_events.jsonl"

    with output_path.open("w", encoding="utf-8") as handle:
        for event in all_events:
            handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    print(
        f"wrote {len(all_events)} events to {output_path} "
        f"(blocks {start_block}-{end_block})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
