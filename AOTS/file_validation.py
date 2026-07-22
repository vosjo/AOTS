"""
File upload validation helpers (images + science file magic bytes).

Named ``file_validation`` (not ``upload_*``) so it is not excluded by .gitignore.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError


def validate_image_upload(uploaded_file):
    """Reject non-image uploads (SVG/HTML/etc.) using Pillow verify."""
    name = (getattr(uploaded_file, 'name', '') or '').lower()
    if name.endswith(('.svg', '.svgz', '.html', '.htm', '.xhtml', '.xml')):
        raise ValidationError('SVG/HTML uploads are not allowed.')

    try:
        from PIL import Image
    except ImportError as exc:
        raise ValidationError('Image validation unavailable.') from exc

    pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.verify()
        fmt = (image.format or '').upper()
        if fmt not in {'PNG', 'JPEG', 'WEBP'}:
            raise ValidationError('Only PNG, JPEG, and WebP images are allowed.')
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError('Invalid or corrupted image file.') from exc
    finally:
        try:
            uploaded_file.seek(pos)
        except Exception:
            pass


def _read_prefix(uploaded_file, nbytes: int = 16) -> bytes:
    pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read(nbytes)
    finally:
        try:
            uploaded_file.seek(pos)
        except Exception:
            pass
    return data or b''


def validate_science_upload(uploaded_file, *, allow_fits=True, allow_hdf5=True, allow_text=False):
    """
    Validate common astronomy upload formats by magic bytes / extension whitelist.
    """
    name = (getattr(uploaded_file, 'name', '') or '').lower()
    prefix = _read_prefix(uploaded_file, 16)

    if allow_fits and (prefix.startswith(b'SIMPLE') or name.endswith(('.fits', '.fit', '.fts'))):
        if prefix and not prefix.startswith(b'SIMPLE'):
            raise ValidationError('Invalid FITS file (missing SIMPLE keyword).')
        return

    if allow_hdf5 and (
        prefix.startswith(b'\x89HDF\r\n\x1a\n') or name.endswith(('.h5', '.hdf5', '.hdf'))
    ):
        if not prefix.startswith(b'\x89HDF\r\n\x1a\n'):
            raise ValidationError('Invalid HDF5 file.')
        return

    if allow_text and name.endswith(('.csv', '.txt', '.dat', '.tsv')):
        sample = prefix[:16].lstrip().lower()
        if sample.startswith(b'<') or sample.startswith(b'<!doctype'):
            raise ValidationError('HTML/SVG content is not allowed for text uploads.')
        return

    allowed = []
    if allow_fits:
        allowed.append('FITS')
    if allow_hdf5:
        allowed.append('HDF5')
    if allow_text:
        allowed.append('CSV/TXT')
    raise ValidationError('Unsupported file type. Allowed: ' + ', '.join(allowed))
