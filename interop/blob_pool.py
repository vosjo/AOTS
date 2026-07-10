"""Resolve ASTRA .astra blob pool indices to bytes/doubles."""

from __future__ import annotations

import struct
from typing import Any


class BlobReader:
    def __init__(self, pool: bytes, directory: list[dict[str, Any]]):
        self.pool = pool
        self.directory = directory

    def _entry(self, index: int) -> tuple[int, int] | None:
        if index is None or index < 0 or index >= len(self.directory):
            return None
        entry = self.directory[index]
        offset = int(entry.get('o', -1))
        length = int(entry.get('l', -1))
        if offset < 0 or length <= 0 or offset + length > len(self.pool):
            return None
        return offset, length

    def get_bytes(self, index: int) -> bytes:
        span = self._entry(index)
        if not span:
            return b''
        offset, length = span
        return self.pool[offset:offset + length]

    def get_doubles(self, index: int) -> list[float]:
        raw = self.get_bytes(index)
        if not raw:
            return []
        count = len(raw) // 8
        return list(struct.unpack(f'<{count}d', raw[: count * 8]))


class BlobPool:
    def __init__(self):
        self.data = bytearray()
        self.directory: list[dict[str, float]] = []

    def add_doubles(self, values: list[float]) -> int:
        if not values:
            return -1
        offset = len(self.data)
        payload = struct.pack(f'<{len(values)}d', *values)
        self.data.extend(payload)
        self.directory.append({'o': float(offset), 'l': float(len(payload))})
        return len(self.directory) - 1

    def add_bytes(self, values: bytes) -> int:
        if not values:
            return -1
        offset = len(self.data)
        self.data.extend(values)
        self.directory.append({'o': float(offset), 'l': float(len(values))})
        return len(self.directory) - 1

    @property
    def bytes(self) -> bytes:
        return bytes(self.data)
