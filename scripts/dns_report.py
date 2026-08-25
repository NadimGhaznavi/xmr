#!/usr/bin/env python3
"""Report the CNAME targets for the deployment's service DNS names."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from constants.DHost import DNS_RECORDS, DNSRecord  # noqa: E402

NOT_FOUND = "NOT FOUND"
DigRunner = Callable[..., subprocess.CompletedProcess[str]]


def cname_target(name: str, runner: DigRunner = subprocess.run) -> str:
    """Return the first CNAME target reported by dig, without its trailing dot."""
    result = runner(
        ["dig", "+short", "+time=2", "+tries=1", "CNAME", name],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return NOT_FOUND

    target = next((line.strip() for line in result.stdout.splitlines() if line), "")
    return target.removesuffix(".") if target else NOT_FOUND


def render_report(rows: Sequence[tuple[DNSRecord, str]]) -> str:
    """Render DNS records and their targets as an aligned text table."""
    headings = ("Environment", "Service", "DNS name", "Resolves to")
    values = [
        (record.environment, record.service, record.name, target)
        for record, target in rows
    ]
    widths = [
        max(len(headings[index]), *(len(row[index]) for row in values))
        for index in range(len(headings))
    ]

    def format_row(row: Sequence[str]) -> str:
        return "  ".join(value.ljust(width) for value, width in zip(row, widths))

    separator = "  ".join("-" * width for width in widths)
    return "\n".join((format_row(headings), separator, *(format_row(row) for row in values)))


def main() -> int:
    if shutil.which("dig") is None:
        print("This report requires the 'dig' command.", file=sys.stderr)
        return 2

    with ThreadPoolExecutor(max_workers=min(8, len(DNS_RECORDS))) as executor:
        targets = executor.map(cname_target, (record.name for record in DNS_RECORDS))
        rows = list(zip(DNS_RECORDS, targets))
    print(render_report(rows))
    return int(any(target == NOT_FOUND for _, target in rows))


if __name__ == "__main__":
    raise SystemExit(main())
