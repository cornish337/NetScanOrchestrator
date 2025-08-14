"""Utilities for planning scan jobs by splitting targets."""

from __future__ import annotations

from typing import Sequence, List, Any


def split_fixed_size(items: Sequence[Any], size: int) -> List[List[Any]]:
    """Split *items* into chunks of a fixed *size*.

    Parameters
    ----------
    items:
        Sequence of items to split.
    size:
        Maximum number of items per chunk.  Must be greater than zero.

    Returns
    -------
    list[list[Any]]
        Chunks of *items* no larger than *size*.
    """

    if size <= 0:
        raise ValueError("size must be positive")
    return [list(items[i : i + size]) for i in range(0, len(items), size)]


def split_binary(items: Sequence[Any], max_chunk_size: int) -> List[List[Any]]:
    """Recursively split *items* into halves until each chunk is within
    ``max_chunk_size``.

    This implements a simple binary splitting strategy which is useful for
    balancing work when the total number of items is not known in advance.

    Parameters
    ----------
    items:
        Sequence of items to split.
    max_chunk_size:
        Desired maximum size of each resulting chunk.  Must be greater than
        zero.

    Returns
    -------
    list[list[Any]]
        Chunks of *items* where each chunk has at most ``max_chunk_size``
        elements.
    """

    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive")

    items = list(items)
    if len(items) <= max_chunk_size:
        return [items]

    mid = len(items) // 2
    left = split_binary(items[:mid], max_chunk_size)
    right = split_binary(items[mid:], max_chunk_size)
    return left + right


__all__ = ["split_fixed_size", "split_binary"]

