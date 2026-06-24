"""Import alternative names for a star from Simbad."""

from __future__ import annotations

from dataclasses import dataclass, field

from astroquery.simbad import Simbad

from stars.auxil import _simbad_field, query_simbad_object
from stars.models import Identifier, Star


def simbad_ident_href(name: str) -> str:
    ident = name.replace(' ', '').replace('+', '%2B')
    return f'https://simbad.u-strasbg.fr/simbad/sim-id?Ident={ident}'


@dataclass
class SimbadIdentifiersResult:
    status: str
    message: str
    added: int = 0
    skipped: int = 0
    total_simbad: int = 0
    warnings: list[str] = field(default_factory=list)


def _query_simbad_identifiers(name: str) -> list[str] | None:
    name = (name or '').strip()
    if not name:
        return None
    try:
        tbl = Simbad.query_objectids(name)
    except Exception:
        return None
    if tbl is None or len(tbl) == 0:
        return None
    return [
        str(row['id']).strip()
        for row in tbl
        if str(row['id']).strip()
    ]


def _resolve_simbad_identifier_names(star: Star) -> list[str] | None:
    names = _query_simbad_identifiers(star.name)
    if names:
        return names

    row = query_simbad_object(star.name)
    if row is not None:
        main_id = str(_simbad_field(row, 'main_id', 'MAIN_ID') or '').strip()
        if main_id:
            names = _query_simbad_identifiers(main_id)
            if names:
                return names

    for ident in star.identifier_set.all():
        names = _query_simbad_identifiers(ident.name)
        if names:
            return names
    return None


def sync_simbad_identifiers(star: Star) -> SimbadIdentifiersResult:
    names = _resolve_simbad_identifier_names(star)
    if not names:
        return SimbadIdentifiersResult(
            status='not_found',
            message=f'No Simbad identifiers found for {star.name!r}.',
        )

    existing = {ident.name for ident in star.identifier_set.all()}
    added = 0
    skipped = 0
    for name in names:
        if name in existing:
            skipped += 1
            continue
        Identifier.objects.create(
            star=star,
            project=star.project,
            name=name,
            href=simbad_ident_href(name),
        )
        existing.add(name)
        added += 1

    primary = star.identifier_set.filter(name=star.name).first()
    if primary is not None and not primary.href:
        primary.href = simbad_ident_href(star.name)
        primary.save(update_fields=['href'])

    if added == 0:
        message = f'All {len(names)} Simbad identifiers were already present.'
    else:
        message = (
            f'Added {added} identifier(s) from Simbad'
            f' ({skipped} already present).'
        )

    return SimbadIdentifiersResult(
        status='ok',
        message=message,
        added=added,
        skipped=skipped,
        total_simbad=len(names),
    )


def accumulate_simbad_bulk_summary(summary, star, result: SimbadIdentifiersResult) -> None:
    if result.status == 'ok':
        summary['ok'] += 1
        summary['added_total'] += result.added
        return
    if result.status == 'not_found':
        summary['no_match'] += 1
        return
    summary['failed'] += 1
    summary['errors'].append({
        'star_pk': star.pk,
        'star_name': star.name,
        'message': result.message,
    })
