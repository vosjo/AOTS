
from django.apps import AppConfig


class StarsConfig(AppConfig):
    name = 'stars'

    def ready(self):
        from stars import signals  # noqa: F401
