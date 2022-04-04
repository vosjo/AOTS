import re

from spectra.models import Spectrum


def search_spectra(q):
    """
    Handles a few default keyword searches
    """

    # one date as HJD
    m = re.compile("^245\d\d\d\d\.??\d*?$").match(q)
    if m:
        delta = 0.01 if '.' in m.group() else 1
        hjd_q = float(m.group())
        return Spectrum.objects.filter(hjd__lte=hjd_q + delta).filter(hjd__gte=hjd_q - delta)

    # two dates as HJD
    m = re.compile("^245\d\d\d\d\.??\d*?\s*?-\s*?245\d\d\d\d\.??\d*?$").match(q)
    if m:
        hjds = m.group().split('-')
        hjd1, hjd2 = float(hjds[0]), float(hjds[1])
        return Spectrum.objects.filter(hjd__lte=hjd2).filter(hjd__gte=hjd1)

    # match instrument or telescope
    else:
        return Spectrum.objects.filter(instrument__icontains=q.strip()) | Spectrum.objects.filter(
            telescope__icontains=q.strip())
