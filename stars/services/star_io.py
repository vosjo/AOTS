"""Explicit write API for Star / Identifier (replaces Django signal bookkeeping)."""

from __future__ import annotations

from stars.models import Identifier, Star


def ensure_primary_identifier(star: Star) -> Identifier:
    """Get-or-create an identifier with the same name as the star."""
    try:
        return Identifier.objects.get(name=star.name, star=star)
    except Identifier.DoesNotExist:
        return Identifier.objects.create(name=star.name, star=star)


def after_star_saved(star: Star) -> None:
    ensure_primary_identifier(star)


def create_star(*, name, project, ra=0.0, dec=0.0, **fields) -> Star:
    star = Star(name=name, project=project, ra=ra, dec=dec, **fields)
    star.save()
    after_star_saved(star)
    return star


def save_star(star: Star) -> Star:
    star.save()
    after_star_saved(star)
    return star
