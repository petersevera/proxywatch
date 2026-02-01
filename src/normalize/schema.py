from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EventType = Literal["upgraded", "admin_changed", "beacon_upgraded"]
Source = Literal["onchain", "manual"]
Chain = Literal["ethereum"]


class UpgradeEvent(BaseModel):
    schema_version: str = Field(default="0.1")
    event_id: str = Field(min_length=8)
    event_type: EventType
    source: Source
    chain: Chain = "ethereum"
    proxy_address: str
    implementation_address: Optional[str] = None
    admin_address: Optional[str] = None
    beacon_address: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    log_index: Optional[int] = None
    event_time: datetime
    ingest_time: Optional[datetime] = None
    raw: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_time", "ingest_time")
    @classmethod
    def _tz_aware(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    @field_validator("proxy_address", "implementation_address", "admin_address", "beacon_address")
    @classmethod
    def _address_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.startswith("0x") or len(value) != 42:
            raise ValueError("address must be 0x + 40 hex chars")
        return value

    @field_validator("tx_hash")
    @classmethod
    def _tx_hash_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.startswith("0x") or len(value) != 66:
            raise ValueError("tx_hash must be 0x + 64 hex chars")
        return value

    @model_validator(mode="after")
    def _cross_fields(self) -> "UpgradeEvent":
        if self.event_type == "upgraded" and not self.implementation_address:
            raise ValueError("implementation_address required for upgraded events")
        if self.event_type == "admin_changed" and not self.admin_address:
            raise ValueError("admin_address required for admin_changed events")
        if self.event_type == "beacon_upgraded" and not self.beacon_address:
            raise ValueError("beacon_address required for beacon_upgraded events")

        if self.source == "onchain":
            if not self.tx_hash or self.block_number is None:
                raise ValueError("tx_hash and block_number required for onchain events")

        return self
