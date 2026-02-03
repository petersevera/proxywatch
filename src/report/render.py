from __future__ import annotations

from typing import Dict, Iterable, List


def _truncate(items: Iterable[str], limit: int) -> List[str]:
    values = list(items)
    if limit <= 0 or len(values) <= limit:
        return values
    return values[:limit]


def render_markdown(report: Dict[str, object], max_selectors: int = 20) -> str:
    selectors = report.get("selectors", {})
    added = selectors.get("added", [])
    removed = selectors.get("removed", [])

    added_list = _truncate(added, max_selectors)
    removed_list = _truncate(removed, max_selectors)

    lines = [
        "# ProxyWatch Upgrade Report",
        "",
        f"Report ID: `{report.get('report_id')}`",
        f"Generated: {report.get('generated_at')}",
        "",
        "## Upgrade",
        f"- Proxy: `{report.get('proxy_address')}`",
        f"- Chain: `{report.get('chain')}`",
        f"- Event ID: `{report.get('event_id')}`",
        f"- Tx: `{report.get('tx_hash')}`",
        f"- Block: `{report.get('block_number')}`",
        f"- Event time: {report.get('event_time')}",
        "",
        "## Implementation",
        f"- Previous: `{report.get('previous_implementation')}`",
        f"- Current: `{report.get('new_implementation')}`",
        "",
        "## Bytecode",
        f"- Previous hash: `{report.get('bytecode', {}).get('previous_hash')}`",
        f"- Current hash: `{report.get('bytecode', {}).get('current_hash')}`",
        f"- Previous size: `{report.get('bytecode', {}).get('previous_size')}`",
        f"- Current size: `{report.get('bytecode', {}).get('current_size')}`",
        f"- Changed: `{report.get('bytecode', {}).get('changed')}`",
        "",
        "## Selector diff",
        f"- Total previous: `{selectors.get('total_previous')}`",
        f"- Total current: `{selectors.get('total_current')}`",
        f"- Unchanged: `{selectors.get('unchanged')}`",
        f"- Added: `{len(added)}`",
        f"- Removed: `{len(removed)}`",
        "",
    ]

    if added_list:
        lines.append("### Added selectors")
        lines.extend([f"- `{selector}`" for selector in added_list])
        if len(added) > len(added_list):
            lines.append(f"- ... ({len(added) - len(added_list)} more)")
        lines.append("")

    if removed_list:
        lines.append("### Removed selectors")
        lines.extend([f"- `{selector}`" for selector in removed_list])
        if len(removed) > len(removed_list):
            lines.append(f"- ... ({len(removed) - len(removed_list)} more)")
        lines.append("")

    notes = report.get("notes") or []
    if notes:
        lines.append("## Notes")
        lines.extend([f"- {note}" for note in notes])
        lines.append("")

    return "\n".join(lines).strip() + "\n"
