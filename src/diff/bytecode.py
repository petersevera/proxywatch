from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import json

from web3 import Web3

from diff.selectors import extract_selectors


@dataclass(frozen=True)
class BytecodeSummary:
    size: int
    code_hash: Optional[str]
    selectors: set[str]


def _to_bytes(bytecode_hex: str) -> bytes:
    if not bytecode_hex:
        return b""
    cleaned = bytecode_hex[2:] if bytecode_hex.startswith("0x") else bytecode_hex
    if cleaned == "":
        return b""
    return bytes.fromhex(cleaned)


def _hash_bytecode(bytecode: bytes) -> Optional[str]:
    if not bytecode:
        return None
    return Web3.to_hex(Web3.keccak(bytecode))


def summarize_bytecode(bytecode_hex: str) -> BytecodeSummary:
    bytecode = _to_bytes(bytecode_hex)
    return BytecodeSummary(
        size=len(bytecode),
        code_hash=_hash_bytecode(bytecode),
        selectors=extract_selectors(bytecode),
    )


def _canonical_address(address: str) -> str:
    try:
        return Web3.to_checksum_address(address)
    except ValueError:
        return address.lower()


def load_bytecode_cache(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {k: str(v) for k, v in payload.items()}


def save_bytecode_cache(path: Path, cache: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_bytecode(w3: Web3, address: str, cache: Dict[str, str]) -> str:
    canonical = _canonical_address(address)
    if canonical in cache:
        return cache[canonical]
    code = w3.eth.get_code(canonical)
    code_hex = Web3.to_hex(code)
    cache[canonical] = code_hex
    return code_hex
