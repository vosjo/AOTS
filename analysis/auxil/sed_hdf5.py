"""SED-fit HDF5 axis metadata (generic DATA/MODEL and ISIS master layouts)."""

from __future__ import annotations

import h5py

# Canonical values stored in HDF5 group attributes (machine-readable).
SED_XLABEL = 'Wavelength'
SED_XUNIT = 'Angstrom'
SED_YLABEL = 'Flux density F_lambda'
SED_YUNIT = 'erg/s/cm2/AA'

_BARE_YLABELS = frozenset({'flux', 'flam', 'flambda', 'f_lambda', 'f'})
_GENERIC_SED_TYPES = frozenset({'sedfit', 'sed', 'sed_fit'})


def is_generic_sedfit_hdf5(hdf: h5py.File | h5py.Group) -> bool:
    """True for AOTS sedfit layout (DATA + MODEL groups)."""
    return 'DATA' in hdf and 'MODEL' in hdf


def is_sed_fit_file(hdf: h5py.File | h5py.Group) -> bool:
    """True when the file should carry SED flux-density axis metadata."""
    ftype = str(hdf.attrs.get('type', '') or '').lower()
    if ftype in _GENERIC_SED_TYPES or ftype == 'sf':
        return True
    if is_generic_sedfit_hdf5(hdf):
        return True
    if 'master' in hdf and 'results' in hdf:
        return True
    return False


def _needs_group_axis_patch(grp: h5py.Group) -> bool:
    yunit = grp.attrs.get('yunit')
    if yunit is None or str(yunit).strip() == '':
        return True
    ylabel = str(grp.attrs.get('ylabel', '') or '').strip().lower()
    return ylabel in _BARE_YLABELS


def apply_sed_axis_attrs(
    grp: h5py.Group,
    *,
    xscale: str | None = None,
    yscale: str | None = None,
) -> None:
    """Write standard SED axis labels and units onto an HDF5 group."""
    grp.attrs['xlabel'] = SED_XLABEL
    grp.attrs['xunit'] = SED_XUNIT
    grp.attrs['ylabel'] = SED_YLABEL
    grp.attrs['yunit'] = SED_YUNIT
    if xscale is not None:
        grp.attrs['xscale'] = xscale
    elif 'xscale' not in grp.attrs:
        grp.attrs['xscale'] = 'log'
    if yscale is not None:
        grp.attrs['yscale'] = yscale
    elif 'yscale' not in grp.attrs:
        grp.attrs['yscale'] = 'log'


def ensure_sedfit_axis_metadata(path: str) -> bool:
    """
    Patch an on-disk SED HDF5 file with axis units when missing.

    Returns True when the file was modified.
    """
    modified = False
    with h5py.File(path, 'r+') as hdf:
        if not is_sed_fit_file(hdf):
            return False

        groups: list[h5py.Group] = []
        if is_generic_sedfit_hdf5(hdf):
            groups.extend(hdf[name] for name in ('DATA', 'MODEL') if name in hdf)
        if 'master' in hdf:
            groups.append(hdf['master'])

        for grp in groups:
            if not _needs_group_axis_patch(grp):
                continue
            xscale = str(grp.attrs.get('xscale', 'log') or 'log')
            yscale = str(grp.attrs.get('yscale', 'log') or 'log')
            apply_sed_axis_attrs(grp, xscale=xscale, yscale=yscale)
            modified = True

    return modified
