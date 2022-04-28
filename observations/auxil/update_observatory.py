from django.shortcuts import get_object_or_404

from observations.models import Observatory


def update_observatory(cleaned_data):
    obs = get_object_or_404(Observatory, pk=cleaned_data["pk"])
    obs.name = cleaned_data["name"]
    obs.short_name = cleaned_data["short_name"]
    obs.telescopes = cleaned_data["telescopes"]
    obs.latitude = cleaned_data["latitude"]
    obs.longitude = cleaned_data["longitude"]
    obs.altitude = cleaned_data["altitude"]
    obs.space_craft = cleaned_data["space_craft"]
    obs.note = cleaned_data["note"]
    obs.url = cleaned_data["url"]
    obs.weatherurl = cleaned_data["weatherurl"]
    obs.save()
    return True, ""
