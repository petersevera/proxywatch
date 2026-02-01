# Architecture

## System flow

[Watchlist]
  - Proxy addresses to monitor
        |
        v
[Ingest]
  - On-chain logs (Upgraded/AdminChanged/BeaconUpgraded)
        |
        v
[Normalize]
  - Canonical event schema
  - Event-time ordering + dedupe
        |
        v
[Store]
  - Upgrade ledger per proxy
        |
        v
[Diff]
  - Bytecode + selector diff
  - Optional storage layout diff
        |
        v
[Report]
  - Markdown + JSON outputs
        |
        v
[API/CLI]
  - Read-only queries

## Core design decisions
- Everything is reproducible from on-chain logs.
- Event-time semantics to preserve order.
- Reports include raw tx hash for auditing.

## Security considerations
- No private keys required.
- No on-chain writes.
- Reports are deterministic and traceable.
