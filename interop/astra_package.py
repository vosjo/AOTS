"""
Read/write ASTRA .astra star packages (StarPackage v1.0).
"""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass, field
from typing import Any

from interop.blob_pool import BlobPool, BlobReader

MAGIC = b'ASTRAPKG'
HEADER_SIZE = 20
VERSION_MAJOR = 1
VERSION_MINOR = 0


@dataclass
class AstraPackage:
    manifest: dict[str, Any]
    pool: bytes
    version_major: int = VERSION_MAJOR
    version_minor: int = VERSION_MINOR
    warnings: list[str] = field(default_factory=list)

    @property
    def stars(self) -> list[dict[str, Any]]:
        return self.manifest.get('stars') or []

    @property
    def instruments(self) -> list[dict[str, Any]]:
        return self.manifest.get('instruments') or []

    def blob_reader(self) -> BlobReader:
        return BlobReader(self.pool, self.manifest.get('blobs') or [])


def _quncompress(data: bytes) -> bytes:
    if len(data) < 4:
        raise ValueError('Corrupt compressed body')
    return zlib.decompress(data[4:])


def _qcompress(data: bytes, level: int = 6) -> bytes:
    compressed = zlib.compress(data, level)
    header = struct.pack('>I', len(data))
    return header + compressed


def read_astra_package(raw: bytes) -> AstraPackage:
    if len(raw) < HEADER_SIZE or raw[:8] != MAGIC:
        raise ValueError('Not an ASTRA package (bad magic)')

    version_major, version_minor = struct.unpack_from('<HH', raw, 8)
    if version_major > VERSION_MAJOR:
        raise ValueError(
            f'File format v{version_major}.{version_minor} is newer than supported '
            f'v{VERSION_MAJOR}.{VERSION_MINOR}'
        )

    warnings: list[str] = []
    if version_major < VERSION_MAJOR:
        warnings.append(f'Reading older package format v{version_major}.{version_minor}.')

    inner = _quncompress(raw[HEADER_SIZE:])
    if len(inner) < 4:
        raise ValueError('Corrupt or empty package body')

    manifest_len = struct.unpack_from('<I', inner, 0)[0]
    if 4 + manifest_len > len(inner):
        raise ValueError('Corrupt manifest length')

    manifest = json.loads(inner[4:4 + manifest_len].decode('utf-8'))
    if manifest.get('format') != 'astra-package':
        raise ValueError('Manifest is not an astra-package')

    pool = inner[4 + manifest_len:]
    return AstraPackage(
        manifest=manifest,
        pool=pool,
        version_major=version_major,
        version_minor=version_minor,
        warnings=warnings,
    )


def write_astra_package(
    stars: list[dict[str, Any]],
    *,
    instruments: list[dict[str, Any]] | None = None,
    blob_pool: BlobPool | None = None,
    creator_note: str = '',
    created_by: str = 'AOTS',
) -> bytes:
    bp = blob_pool or BlobPool()
    manifest = {
        'format': 'astra-package',
        'versionMajor': VERSION_MAJOR,
        'versionMinor': VERSION_MINOR,
        'createdBy': created_by,
        'createdAt': _iso_now(),
        'stars': stars,
        'instruments': instruments or [],
        'blobs': bp.directory,
    }
    if creator_note:
        manifest['note'] = creator_note

    manifest_bytes = json.dumps(manifest, separators=(',', ':')).encode('utf-8')
    inner = struct.pack('<I', len(manifest_bytes)) + manifest_bytes + bp.bytes
    body = _qcompress(inner)

    header = bytearray()
    header.extend(MAGIC)
    header.extend(struct.pack('<HH', VERSION_MAJOR, VERSION_MINOR))
    header.extend(struct.pack('<B', 0))  # byte order
    header.extend(struct.pack('<B', 0))
    header.extend(struct.pack('<H', 0))
    header.extend(struct.pack('<I', 0))
    return bytes(header) + body


def _iso_now() -> str:
    from django.utils import timezone
    return timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ')
