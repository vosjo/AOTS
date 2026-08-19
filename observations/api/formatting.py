from astropy.coordinates import Angle
from astropy.time import Time

EMPTY_DISPLAY = '—'


def dgr2hms(value):
    try:
        a = Angle(float(value), unit='degree').hms
        return '{:02.0f}:{:02.0f}:{:05.2f}'.format(*a)
    except (TypeError, ValueError):
        return str(value)


def dgr2dms(value):
    try:
        a = Angle(float(value), unit='degree').dms
        return f'{a[0]:+03.0f}:{abs(a[1]):02.0f}:{abs(a[2]):05.2f}'
    except (TypeError, ValueError):
        return str(value)


def hjd2date(hjd):
    t = Time(float(hjd), format='jd')
    t.format = 'iso'
    t.out_subfmt = 'date'
    return t.iso


def hjd2datetime(hjd):
    t = Time(float(hjd), format='jd')
    t.format = 'iso'
    t.out_subfmt = 'date_hms'
    return t.iso


def dgr2cardinal(degrees):
    if degrees < 0 or degrees > 360:
        return EMPTY_DISPLAY
    if degrees > 337.5 or degrees < 22.5:
        return 'N'
    if degrees < 67.5:
        return 'NE'
    if degrees < 112.5:
        return 'E'
    if degrees < 157.5:
        return 'SE'
    if degrees < 202.5:
        return 'S'
    if degrees < 247.5:
        return 'SW'
    if degrees < 292.5:
        return 'W'
    return 'NW'


def format_float_negative_na(value, decimals=0, unit=''):
    if value is None or value < 0:
        return EMPTY_DISPLAY
    formatted = f'{value:.{decimals}f}'
    if unit:
        return f'{formatted} {unit}'
    return formatted


def format_wind_direction(direction):
    if direction is None or direction < 0:
        return EMPTY_DISPLAY
    return f'{direction:.0f}° ({dgr2cardinal(direction)})'


def format_wind(speed, direction):
    speed_str = format_float_negative_na(speed, decimals=1, unit='km/s')
    if speed_str == EMPTY_DISPLAY:
        return speed_str
    return f'{speed_str} {format_wind_direction(direction)}'
