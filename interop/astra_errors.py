"""Map AOTS err_l/err_u ↔ ASTRA symmetric + ErrUp/ErrDown (see ASTRA AsymErr)."""

from __future__ import annotations

import math
from typing import Any

NEARLY_SYMMETRIC_REL_TOL = 0.10


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def nearly_symmetric(
    err_l: float,
    err_u: float,
    *,
    rel_tol: float = NEARLY_SYMMETRIC_REL_TOL,
) -> bool:
    up, down = float(err_u), float(err_l)
    m = max(abs(up), abs(down))
    if m <= 0.0:
        return True
    return abs(up - down) <= rel_tol * m


def symmetric_error(err_l: float, err_u: float) -> float:
    return 0.5 * (float(err_l) + float(err_u))


def errors_from_aots_raw(raw: Any) -> tuple[float, float, float]:
    """Return (value, err_l, err_u) from an AOTS parameter record."""
    if isinstance(raw, dict):
        value = float(raw.get('value', 0) or 0)
        err_l = float(raw.get('err_l', raw.get('error_l', 0)) or 0)
        err_u = float(raw.get('err_u', raw.get('error_u', err_l)) or 0)
        if 'error' in raw and err_l == 0 and err_u == 0:
            sym = float(raw.get('error', 0) or 0)
            err_l = err_u = sym
        return value, err_l, err_u
    if hasattr(raw, 'colnames') and 'value' in raw.colnames:
        row = raw[0]
        err_l = float(row['err_l']) if 'err_l' in raw.colnames else 0.0
        err_u = float(row['err_u']) if 'err_u' in raw.colnames else err_l
        return float(row['value']), err_l, err_u
    if hasattr(raw, 'dtype') and getattr(raw.dtype, 'names', None):
        row = raw[0]
        err_l = float(row['err_l']) if 'err_l' in raw.dtype.names else 0.0
        err_u = float(row['err_u']) if 'err_u' in raw.dtype.names else err_l
        return float(row['value']), err_l, err_u
    return 0.0, 0.0, 0.0


def err_bounds_from_astra(
    sym: float,
    err_up: Any,
    err_down: Any,
) -> tuple[float, float]:
    """Map ASTRA symmetric + optional Up/Down to AOTS (err_l, err_u)."""
    sym = float(sym or 0)
    up_set = _is_finite(err_up)
    down_set = _is_finite(err_down)
    if up_set or down_set:
        err_u = float(err_up) if up_set else sym
        err_l = float(err_down) if down_set else sym
        return err_l, err_u
    return sym, sym


def read_astra_param_errors(container: dict, err_key: str) -> tuple[float, float, float]:
    """Read (sym, err_l, err_u) from an ASTRA fit JSON object."""
    sym = float(container.get(err_key, 0) or 0)
    err_l, err_u = err_bounds_from_astra(
        sym,
        container.get(f'{err_key}Up'),
        container.get(f'{err_key}Down'),
    )
    return sym, err_l, err_u


def apply_astra_errors(
    out: dict,
    *,
    err_key: str,
    err_l: float,
    err_u: float,
) -> None:
    """Write ASTRA symmetric and optional asymmetric error keys."""
    err_l = float(err_l)
    err_u = float(err_u)
    if err_l <= 0 and err_u <= 0:
        return
    sym = symmetric_error(err_l, err_u)
    out[err_key] = sym
    if not nearly_symmetric(err_l, err_u):
        out[f'{err_key}Up'] = err_u
        out[f'{err_key}Down'] = err_l


def write_astra_param(
    out: dict,
    *,
    value_key: str,
    err_key: str,
    value: float,
    err_l: float,
    err_u: float,
) -> None:
    if value or err_l or err_u:
        out[value_key] = float(value)
        apply_astra_errors(out, err_key=err_key, err_l=err_l, err_u=err_u)
