"""Utilities for parsing and chunking target addresses.

This module provides :func:`expand_targets` which converts an iterable of
strings into individual IP addresses or hostnames.  Lines that are empty or
start with ``#`` are ignored.  CIDR blocks (e.g. ``192.0.2.0/30``) and
hyphenated ranges (e.g. ``192.0.2.1-192.0.2.5``) are expanded into individual
addresses.  A ``max_expand`` guard protects against accidental expansion of
very large ranges.

The existing :func:`chunk_ips` helper is retained for callers that still rely
on it.
"""

from ipaddress import ip_address, ip_network
from typing import Iterable, List, Optional


def expand_targets(lines: Iterable[str], max_expand: int) -> List[str]:
    """Expand targets from ``lines`` into individual addresses.

    Parameters
    ----------
    lines:
        An iterable producing raw lines.  Comment lines starting with ``#``
        and blank lines are ignored.  Inline comments (text after ``#``) are
        stripped.
    max_expand:
        Maximum number of addresses allowed when expanding a single CIDR
        block or hyphenated range.  A :class:`ValueError` is raised if this
        limit would be exceeded.

    Returns
    -------
    List[str]
        A list of individual IP address strings or hostnames.
    """

    targets: List[str] = []

    for raw in lines:
        # Remove inline comments and surrounding whitespace
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        # Try CIDR notation first
        if "/" in line:
            try:
                network = ip_network(line, strict=False)
            except ValueError:
                # Not a valid network; treat as hostname
                targets.append(line)
                continue

            if network.num_addresses > max_expand:
                raise ValueError(
                    f"CIDR {line} expands to {network.num_addresses} addresses, "
                    f"exceeding max_expand={max_expand}"
                )

            for ip in network.hosts():
                targets.append(str(ip))
            continue

        # Hyphenated range
        if "-" in line:
            start_s, end_s = line.split("-", 1)
            try:
                start = ip_address(start_s.strip())
                end = ip_address(end_s.strip())
            except ValueError:
                # If parsing fails, treat as hostname (e.g. a host with a hyphen)
                targets.append(line)
                continue

            if int(end) < int(start):
                raise ValueError(f"Invalid range {line}: end before start")

            count = int(end) - int(start) + 1
            if count > max_expand:
                raise ValueError(
                    f"Range {line} expands to {count} addresses, exceeding max_expand={max_expand}"
                )

            for ip_int in range(int(start), int(end) + 1):
                targets.append(str(ip_address(ip_int)))
            continue

        # Single IP address or hostname
        targets.append(line)

    return targets


def read_ips_from_file(filepath: str, max_expand: int = 4096) -> List[str]:
    """Read targets from ``filepath`` using :func:`expand_targets`.

    The default ``max_expand`` mirrors the guard used when expanding targets
    via the CLI.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        return expand_targets(f, max_expand)


def chunk_ips(
    ips: List[str],
    chunk_size: int = 0,
    custom_ranges: Optional[List[List[str]]] = None,
) -> List[List[str]]:
    """Divide a list of IPs into chunks.

    Parameters
    ----------
    ips:
        List of IP address strings.
    chunk_size:
        Desired size of each chunk.  If ``0`` or less, a single chunk containing
        all IPs is returned.
    custom_ranges:
        If provided, these ranges are returned directly and ``ips`` is ignored.

    Returns
    -------
    List[List[str]]
        Chunks of IP addresses.
    """

    if not ips:
        return []

    if custom_ranges:  # Assuming custom_ranges is list[list[str]]
        return custom_ranges

    if chunk_size > 0:
        return [ips[i : i + chunk_size] for i in range(0, len(ips), chunk_size)]

    return [ips]  # Default to a single chunk if no other criteria met


__all__ = ["expand_targets", "read_ips_from_file", "chunk_ips"]

