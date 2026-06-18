"""Stored-parameter name aliases (no Django model imports)."""

STORED_PARAMETER_ALIASES = {
    'absolute_g_mag': ['mag_abs', 'M_G'],
}


def stored_parameter_lookup_names(canonical_name: str) -> list[str]:
    """DB ``name`` values that refer to the same stored parameter."""
    return [canonical_name, *STORED_PARAMETER_ALIASES.get(canonical_name, [])]
