"""Professional axis titles for analysis HDF5 Bokeh plots."""

from __future__ import annotations

from typing import Any

from analysis.categories import AnalysisCategory, category_for_hdf5

WAVELENGTH_ANGSTROM = 'Wavelength [Å]'
FLUX_DENSITY_F_LAMBDA = 'Flux density Fλ [erg s⁻¹ cm⁻² Å⁻¹]'
RADIAL_VELOCITY = 'Radial velocity [km s⁻¹]'
TIME_AXIS = 'Time [d]'

_SED_FILE_TYPES = frozenset({'sedfit', 'sf', 'sed', 'sed_fit'})

_WAVELENGTH_ALIASES = frozenset({
    'wavelength',
    'wavelength (aa)',
    'wavelength [aa]',
    'wavelength (angstrom)',
    'wave',
    'lambda',
    'wl',
})

_FLUX_ALIASES = frozenset({
    'flux',
    'flam',
    'flambda',
    'f_lambda',
    'fλ',
    'f',
})

_UNIT_NORMALIZE = {
    'aa': 'Å',
    'angstrom': 'Å',
    'angstroms': 'Å',
    'ergs/cm/cm/s/a': 'erg s⁻¹ cm⁻² Å⁻¹',
    'erg/s/cm2/aa': 'erg s⁻¹ cm⁻² Å⁻¹',
    'erg s-1 cm-2 aa-1': 'erg s⁻¹ cm⁻² Å⁻¹',
    'erg s-1 cm-2 angstrom-1': 'erg s⁻¹ cm⁻² Å⁻¹',
    'km/s': 'km s⁻¹',
    'km s-1': 'km s⁻¹',
}


def _decode_attr(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace').strip()
    return str(value).strip()


def read_hdf_attr(node: Any, attr: str, default: str | None = None) -> str | None:
    """Read a string HDF5 attribute (handles bytes)."""
    if node is None or not hasattr(node, 'attrs') or attr not in node.attrs:
        return default
    text = _decode_attr(node.attrs.get(attr))
    return text or default


def _groups_for_metadata(hdf) -> list[Any]:
    groups: list[Any] = []
    for name in ('DATA', 'MODEL', 'master', 'O-C'):
        if name in hdf:
            groups.append(hdf[name])
    return groups


def _first_attr(hdf, attr: str) -> str | None:
    for node in (hdf, * _groups_for_metadata(hdf)):
        value = read_hdf_attr(node, attr)
        if value:
            return value
    return None


def _is_sed_context(hdf, category: str | None) -> bool:
    if category == AnalysisCategory.SED_FIT:
        return True
    ftype = (_first_attr(hdf, 'type') or '').lower()
    if ftype in _SED_FILE_TYPES:
        return True
    try:
        return category_for_hdf5({'type': ftype, 'results': {}}) == AnalysisCategory.SED_FIT and ftype in _SED_FILE_TYPES
    except Exception:
        return False


def _normalize_unit(unit: str) -> str:
    key = unit.strip().lower()
    compact = key.replace(' ', '')
    for candidate in (key, compact):
        if candidate in _UNIT_NORMALIZE:
            return _UNIT_NORMALIZE[candidate]
    # Already a display string (e.g. from PARAMETER tables).
    return unit.strip()


def _format_with_unit(name: str, unit: str | None) -> str:
    if not unit:
        return name
    unit_disp = _normalize_unit(unit)
    if unit_disp.startswith('['):
        return f'{name} {unit_disp}'
    return f'{name} [{unit_disp}]'


def format_axis_label(
    raw: str | None,
    *,
    axis: str,
    unit: str | None = None,
    sed_context: bool = False,
) -> str:
    """Turn HDF5 xlabel/ylabel (+ optional unit) into a display axis title."""
    text = (raw or '').strip()
    if 'f_lambda' in text.lower():
        text = text.replace('F_lambda', 'Fλ').replace('f_lambda', 'Fλ')
    key = text.lower()

    if axis == 'x':
        if not text and sed_context:
            return WAVELENGTH_ANGSTROM
        if key in _WAVELENGTH_ALIASES or 'wavelength' in key:
            return WAVELENGTH_ANGSTROM
        if key == 'time':
            return TIME_AXIS if unit else 'Time'
        if key == 'rv':
            return RADIAL_VELOCITY
        if text and unit:
            return _format_with_unit(text, unit)
        return text or 'x'

    # y-axis
    if not text and sed_context:
        return FLUX_DENSITY_F_LAMBDA
    if key in ('rv', 'radial velocity'):
        return RADIAL_VELOCITY
    if key in _FLUX_ALIASES or key == 'flux':
        if unit:
            return _format_with_unit('Flux density Fλ', unit)
        return FLUX_DENSITY_F_LAMBDA if sed_context else 'Flux'
    if text and unit:
        return _format_with_unit(text, unit)
    if text and ('[' in text or '(' in text):
        return text.replace('(AA)', '[Å]').replace('(aa)', '[Å]')
    return text or 'y'


def resolve_axis_labels(hdf, *, category: str | None = None) -> tuple[str, str]:
    """
    Resolve X/Y axis titles from HDF5 group attributes.

    SED-fit files often store only ``ylabel='flux'``; when ``type`` is sedfit/SF
    or the analysis category is ``sed_fit``, default to Fλ in cgs flux-density units.
  Optional ``xunit`` / ``yunit`` attributes are honoured when present.
    """
    sed_context = _is_sed_context(hdf, category)
    xlabel = _first_attr(hdf, 'xlabel')
    ylabel = _first_attr(hdf, 'ylabel')
    xunit = _first_attr(hdf, 'xunit')
    yunit = _first_attr(hdf, 'yunit')

    x_axis = format_axis_label(xlabel, axis='x', unit=xunit, sed_context=sed_context)
    y_axis = format_axis_label(ylabel, axis='y', unit=yunit, sed_context=sed_context)
    return x_axis, y_axis
