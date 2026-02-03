from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from normalize.schema import UpgradeEvent
from diff.bytecode import BytecodeSummary


@dataclass(frozen=True)
class UpgradeReport:
    report_id: str
    generated_at: datetime
    proxy_address: str
    chain: str
    event_id: str
    tx_hash: Optional[str]
    block_number: Optional[int]
    event_time: datetime
    previous_implementation: Optional[str]
    new_implementation: str
    bytecode: Dict[str, object]
    selectors: Dict[str, object]
    notes: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "proxy_address": self.proxy_address,
            "chain": self.chain,
            "event_id": self.event_id,
            "tx_hash": self.tx_hash,
            "block_number": self.block_number,
            "event_time": self.event_time.isoformat(),
            "previous_implementation": self.previous_implementation,
            "new_implementation": self.new_implementation,
            "bytecode": self.bytecode,
            "selectors": self.selectors,
            "notes": self.notes,
        }


def build_report(
    event: UpgradeEvent,
    previous_impl: Optional[str],
    previous_summary: Optional[BytecodeSummary],
    current_summary: BytecodeSummary,
    selector_diff: Dict[str, object],
) -> UpgradeReport:
    notes: List[str] = []
    if previous_impl is None:
        notes.append("first upgrade event in range")
    elif previous_impl == event.implementation_address:
        notes.append("implementation address did not change")

    bytecode = {
        "previous_hash": previous_summary.code_hash if previous_summary else None,
        "current_hash": current_summary.code_hash,
        "previous_size": previous_summary.size if previous_summary else None,
        "current_size": current_summary.size,
        "changed": (
            previous_summary is None
            or previous_summary.code_hash != current_summary.code_hash
        ),
    }

    report_id = f"report:{event.event_id}"

    return UpgradeReport(
        report_id=report_id,
        generated_at=datetime.now(timezone.utc),
        proxy_address=event.proxy_address,
        chain=event.chain,
        event_id=event.event_id,
        tx_hash=event.tx_hash,
        block_number=event.block_number,
        event_time=event.event_time,
        previous_implementation=previous_impl,
        new_implementation=event.implementation_address or "",
        bytecode=bytecode,
        selectors=selector_diff,
        notes=notes,
    )
