from __future__ import annotations

from typing import Dict, Set


PUSH4_OPCODE = 0x63


def extract_selectors(bytecode: bytes) -> Set[str]:
    selectors: Set[str] = set()
    i = 0
    size = len(bytecode)
    while i + 4 < size:
        if bytecode[i] == PUSH4_OPCODE:
            selector = "0x" + bytecode[i + 1 : i + 5].hex()
            selectors.add(selector)
            i += 5
            continue
        i += 1
    return selectors


def diff_selectors(previous: Set[str], current: Set[str]) -> Dict[str, object]:
    added = sorted(current - previous)
    removed = sorted(previous - current)
    unchanged = len(previous & current)
    return {
        "added": added,
        "removed": removed,
        "total_previous": len(previous),
        "total_current": len(current),
        "unchanged": unchanged,
    }
