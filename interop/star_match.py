"""Match ASTRA star objects to existing AOTS stars."""

from __future__ import annotations

import math
import re

from django.db.models import Q

from interop.models import InteropRecord
from stars.models import Identifier, Star


GAIA_NUM_RE = re.compile(r'(\d{10,})')
POSITION_TOLERANCE_DEG = 2.0 / 3600.0


def normalize_source_id(source_id: str) -> str:
    source_id = (source_id or '').strip()
    if not source_id:
        return ''
    match = GAIA_NUM_RE.search(source_id)
    if match:
        return match.group(1)
    return source_id


def _position_match(star: Star, ra: float, dec: float) -> bool:
    if ra is None or dec is None:
        return True
    if not star.ra and not star.dec:
        return True
    dra = abs(star.ra - ra) * math.cos(math.radians(dec))
    ddec = abs(star.dec - dec)
    return math.hypot(dra, ddec) <= POSITION_TOLERANCE_DEG


def find_star_by_interop(project, astra_id: str) -> Star | None:
    record = InteropRecord.objects.filter(
        source=InteropRecord.SOURCE_ASTRA,
        external_id=astra_id,
        content_type__app_label='stars',
        content_type__model='star',
    ).select_related('content_type').first()
    if not record:
        return None
    try:
        star = Star.objects.get(pk=record.object_id, project=project)
        return star
    except Star.DoesNotExist:
        return None


def match_star(project, astra_star: dict) -> Star | None:
    astra_id = astra_star.get('id') or ''
    if astra_id:
        found = find_star_by_interop(project, astra_id)
        if found:
            return found

    ra = float(astra_star.get('ra') or 0)
    dec = float(astra_star.get('dec') or 0)
    source_id = normalize_source_id(astra_star.get('sourceId') or '')
    tic = (astra_star.get('tic') or '').strip()
    jname = (astra_star.get('jname') or '').strip()
    alias = (astra_star.get('alias') or '').strip()

    if source_id:
        for ident in Identifier.objects.filter(project=project).filter(
            Q(name__iexact=source_id) | Q(name__icontains=source_id),
        ):
            if _position_match(ident.star, ra, dec):
                return ident.star

    if tic:
        ident = Identifier.objects.filter(project=project, name__iexact=tic).first()
        if ident and _position_match(ident.star, ra, dec):
            return ident.star

    if jname:
        ident = Identifier.objects.filter(project=project, name__iexact=jname).first()
        if ident and _position_match(ident.star, ra, dec):
            return ident.star

    if alias:
        star = Star.objects.filter(project=project, name__iexact=alias).first()
        if star and _position_match(star, ra, dec):
            return star

    if ra or dec:
        candidates = Star.objects.filter(
            project=project,
            ra__range=(ra - 0.01, ra + 0.01),
            dec__range=(dec - 0.01, dec + 0.01),
        )
        for star in candidates:
            if _position_match(star, ra, dec):
                return star

    return None


def apply_identifiers(star: Star, astra_star: dict) -> None:
    pairs = []
    alias = (astra_star.get('alias') or '').strip()
    if alias and alias.lower() != star.name.lower():
        pairs.append(alias)
    source_id = (astra_star.get('sourceId') or '').strip()
    if source_id:
        pairs.append(source_id)
    tic = (astra_star.get('tic') or '').strip()
    if tic:
        pairs.append(f'TIC {tic}')
    jname = (astra_star.get('jname') or '').strip()
    if jname:
        pairs.append(jname)

    for name in pairs:
        Identifier.objects.get_or_create(project=star.project, star=star, name=name)
