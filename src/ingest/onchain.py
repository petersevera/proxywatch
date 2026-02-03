from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from eth_abi import decode as abi_decode
from web3 import Web3

from normalize.schema import UpgradeEvent

UPGRADED_SIG = "Upgraded(address)"
ADMIN_CHANGED_SIG = "AdminChanged(address,address)"
BEACON_UPGRADED_SIG = "BeaconUpgraded(address)"


@dataclass(frozen=True)
class ProxyEventSpec:
    event_type: str
    signature: str


DEFAULT_SPECS: List[ProxyEventSpec] = [
    ProxyEventSpec(event_type="upgraded", signature=UPGRADED_SIG),
    ProxyEventSpec(event_type="admin_changed", signature=ADMIN_CHANGED_SIG),
    ProxyEventSpec(event_type="beacon_upgraded", signature=BEACON_UPGRADED_SIG),
]


def _topic0(signature: str) -> str:
    return Web3.to_hex(Web3.keccak(text=signature))


def _block_time(w3: Web3, block_number: int, cache: Dict[int, datetime]) -> datetime:
    if block_number not in cache:
        block = w3.eth.get_block(block_number)
        cache[block_number] = datetime.fromtimestamp(block["timestamp"], timezone.utc)
    return cache[block_number]


def _topic_address(topic_hex: str) -> str:
    if topic_hex.startswith("0x"):
        topic_hex = topic_hex[2:]
    return Web3.to_checksum_address("0x" + topic_hex[-40:])


def _decode_admin_changed(data: str) -> tuple[str, str]:
    payload = bytes.fromhex(data[2:]) if data.startswith("0x") else bytes.fromhex(data)
    previous, new = abi_decode(["address", "address"], payload)
    return Web3.to_checksum_address(previous), Web3.to_checksum_address(new)


def fetch_proxy_events(
    w3: Web3,
    proxy_address: str,
    from_block: int,
    to_block: int,
    chain: str,
    specs: Iterable[ProxyEventSpec] = DEFAULT_SPECS,
) -> List[UpgradeEvent]:
    events: List[UpgradeEvent] = []
    block_cache: Dict[int, datetime] = {}
    ingest_time = datetime.now(timezone.utc)

    for spec in specs:
        topics = [_topic0(spec.signature)]
        logs = w3.eth.get_logs(
            {
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "address": Web3.to_checksum_address(proxy_address),
                "topics": topics,
            }
        )

        for log in logs:
            block_number = log["blockNumber"]
            log_index = log["logIndex"]
            tx_hash = Web3.to_hex(log["transactionHash"])
            event_time = _block_time(w3, block_number, block_cache)
            impl_address = None
            admin_address = None
            beacon_address = None

            if spec.event_type == "upgraded":
                if len(log["topics"]) > 1:
                    impl_address = _topic_address(Web3.to_hex(log["topics"][1]))
            elif spec.event_type == "admin_changed":
                previous_admin, new_admin = _decode_admin_changed(log["data"])
                admin_address = new_admin
            elif spec.event_type == "beacon_upgraded":
                if len(log["topics"]) > 1:
                    beacon_address = _topic_address(Web3.to_hex(log["topics"][1]))

            event_id = (
                f"{spec.event_type}:{proxy_address}:{tx_hash}:{block_number}:{log_index}"
            )

            events.append(
                UpgradeEvent(
                    event_id=event_id,
                    event_type=spec.event_type,
                    source="onchain",
                    chain=chain,
                    proxy_address=Web3.to_checksum_address(proxy_address),
                    implementation_address=impl_address,
                    admin_address=admin_address,
                    beacon_address=beacon_address,
                    tx_hash=tx_hash,
                    block_number=block_number,
                    log_index=log_index,
                    event_time=event_time,
                    ingest_time=ingest_time,
                    raw={
                        "address": log["address"],
                        "data": Web3.to_hex(log["data"]),
                        "topics": [Web3.to_hex(t) for t in log["topics"]],
                        "topic0": topics[0],
                    },
                )
            )

    return events
