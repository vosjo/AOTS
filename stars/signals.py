"""Signals that invalidate dashboard starmap cache."""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from dash.starmap_cache import invalidate_starmap_cache
from stars.models import Star


@receiver(pre_save, sender=Star)
def _remember_star_coordinates(sender, instance, **kwargs):
    if instance.pk is None:
        instance._starmap_coords_changed = True
        return
    try:
        previous = Star.objects.only('ra', 'dec').get(pk=instance.pk)
    except Star.DoesNotExist:
        instance._starmap_coords_changed = True
        return
    instance._starmap_coords_changed = (
        previous.ra != instance.ra or previous.dec != instance.dec
    )


@receiver(post_save, sender=Star)
def _invalidate_starmap_on_coordinate_change(sender, instance, **kwargs):
    if getattr(instance, '_starmap_coords_changed', False):
        invalidate_starmap_cache(instance.project)
