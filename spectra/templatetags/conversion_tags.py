 
from django import template

from astropy.coordinates.angles import Angle
from astropy.time import Time

register = template.Library()


@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)

@register.filter
def lower(value):
    return value.lower()

@register.filter
def dgr2hms(value):
   try:
      a = Angle(float(value), unit='degree').hms
   except Exception, e:
      return value
   return "{:02.0f}:{:02.0f}:{:05.2f}".format(*a)

@register.filter
def dgr2dms(value):
   try:
      a = Angle(float(value), unit='degree').dms
   except Exception, e:
      return value
   return "{:+03.0f}:{:02.0f}:{:05.2f}".format(a[0], abs(a[1]), abs(a[2]))

@register.filter
def hjd2date(hjd):
   t = Time(hjd, format='jd', out_subfmt='date')
   return t.iso

@register.filter
def hjd2datetime(hjd):
   t = Time(hjd, format='jd', out_subfmt='date_hms')
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