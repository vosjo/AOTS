"""Map ASTRA parameter names to AOTS canonical names."""

from __future__ import annotations

ASTRA_TO_AOTS = {
    'K': ('k', 1),
    'rvK': ('k', 1),
    'gamma': ('v0', 1),
    'rvGamma': ('v0', 1),
    'period': ('p', 0),
    'rvPeriod': ('p', 0),
    't0': ('t0', 0),
    'rvT0': ('t0', 0),
    'phi': ('phi', 0),
    'rvPhi': ('phi', 0),
    'ecc': ('e', 0),
    'rvEcc': ('e', 0),
    'omega': ('omega', 0),
    'rvPhi': ('omega', 0),
    'metal': ('z', 0),
    'teff': ('teff', 1),
    'logg': ('logg', 1),
    'q': ('q', 0),
    'incl': ('incl', 0),
    'photQ': ('q', 0),
    'photIncl': ('incl', 0),
    'photPeriod': ('p', 0),
    'sedMass1': ('m', 1),
    'sedRadius1': ('rad', 1),
    'sedLum1': ('L', 1),
}


def map_parameter_name(astra_name: str) -> tuple[str, int] | None:
    if astra_name in ASTRA_TO_AOTS:
        return ASTRA_TO_AOTS[astra_name]
    lower = astra_name.lower()
    for key, value in ASTRA_TO_AOTS.items():
        if key.lower() == lower:
            return value
    return None
