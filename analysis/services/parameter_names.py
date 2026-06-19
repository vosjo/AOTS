"""Resolve ingested parameter names to canonical base names and components."""

from __future__ import annotations

from analysis.models.default_values import DEFAULT_PARAMETERS, PARAMETER_ALIASES, split_parameter_name


def resolve_ingest_parameter_name(pname: str) -> tuple[str, int] | None:
    """
    Map an ingested parameter key (e.g. ``teff1``, ``met``, ``K1``) to
    ``(canonical_base, component)`` or ``None`` if unsupported.
    """
    base, component = split_parameter_name(pname)

    if base in DEFAULT_PARAMETERS:
        return base, component

    for key in DEFAULT_PARAMETERS:
        if key.lower() == base.lower():
            return key, component

    for canonical, aliases in PARAMETER_ALIASES.items():
        canonical_base, _ = split_parameter_name(canonical)
        if base.lower() == canonical_base.lower():
            return canonical_base, component
        if base.lower() in (alias.lower() for alias in aliases):
            return canonical_base, component
        if pname.lower() in (alias.lower() for alias in aliases):
            return canonical_base, component

    return None


def storage_parameter_name(base: str, component: int) -> str:
    """Build the parameter key used after homogenisation (e.g. ``z1``, ``p``)."""
    if component in (1, 2):
        return f'{base}{component}'
    return base


def normalize_policy_parameter(name: str, component: int) -> tuple[str, int]:
    """
    Canonical policy storage: base parameter name + component field.

    Legacy policies may store ``k1`` with component System; that maps to ``k`` + Primary.
    """
    from analysis.models.default_values import SYSTEM
    from analysis.parameter_labels import normalize_parameter_name

    if name == '*':
        return name, component
    canonical = normalize_parameter_name(name)
    _, suffix_component = split_parameter_name(name)
    if suffix_component in (1, 2) and component == SYSTEM:
        return canonical, suffix_component
    return canonical, component
