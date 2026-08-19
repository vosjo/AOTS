from astropy.coordinates.angles import Angle
from astropy.time import Time
from django import template

register = template.Library()


@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)


@register.filter_function
def filter_filetype(queryset, argument):
    return queryset.filter(filetype__exact=argument)


@register.filter
def lower(value):
    return value.lower()


@register.filter
def dgr2hms(value):
    try:
        a = Angle(float(value), unit='degree').hms
    except Exception:
        return value
    return "{:02.0f}:{:02.0f}:{:05.2f}".format(*a)


@register.filter
def dgr2dms(value):
    try:
        a = Angle(float(value), unit='degree').dms
    except Exception:
        return value
    return f"{a[0]:+03.0f}:{abs(a[1]):02.0f}:{abs(a[2]):05.2f}"


@register.filter
def roundtwo(value):
    return f"{value:.2f}"


@register.filter
def raround(value):
    return f"{value:.4f}"


@register.filter
def degsign(value):
    if value >= 0.:
        return f"+{value:.4f}"
    else:
        return f"-{abs(value):.4f}"


@register.filter
def hjd2date(hjd):
    t = Time(hjd, format='jd')
    t.format = 'iso'
    t.out_subfmt = 'date'
    return t.iso


@register.filter
def hjd2datetime(hjd):
    t = Time(hjd, format='jd')
    t.format = 'iso'
    t.out_subfmt = 'date_hms'
    return t.iso


@register.filter
def dgr2cardinal(degrees):
    """
    Converts degrees to a cardinal direction
    """
    if degrees < 0 or degrees > 360:
        return 'NA'
    if degrees > 337.5 or degrees < 22.5:
        return 'N'
    elif degrees < 67.5:
        return 'NE'
    elif degrees < 112.5:
        return 'E'
    elif degrees < 157.5:
        return 'SE'
    elif degrees < 202.5:
        return 'S'
    elif degrees < 247.5:
        return 'SW'
    elif degrees < 292.5:
        return 'W'
    else:
        return 'NW'


@register.filter
def format_float_negative_na(value, args):
    """
    Formats a float up to a given set of decimals, display NA if negative
    """

    decimals, unit = args.split("|")

    if value >= 0:
        return f"{{:0.{decimals}f}} ".format(value) + unit
    else:
        return "NA"


@register.filter
def format_wind_speed(speed):
    """
    Formats the wind speed and displays NA if not available
    """
    if speed >= 0:
        return f"{speed:0.1f} km/s"
    else:
        return "NA"


@register.filter
def format_wind_direction(direction):
    """
    Formats the wind speed and displays NA if not available
    """
    if direction >= 0:
        return f"{direction:0.0f}° ({dgr2cardinal(direction)}) "
    else:
        return "NA"
