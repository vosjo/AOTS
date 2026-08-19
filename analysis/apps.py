
from django.apps import AppConfig


class AnalysisConfig(AppConfig):
    name = 'analysis'

    def ready(self):
        from django.db.models.signals import post_save

        from analysis.services.consensus_defaults import seed_project_consensus_policies
        from stars.models import Project

        def seed_policies_for_new_project(sender, instance, created, **kwargs):
            if created:
                seed_project_consensus_policies(instance)

        post_save.connect(seed_policies_for_new_project, sender=Project)
