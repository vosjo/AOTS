from django.core.management.base import BaseCommand

from stars.models import Project
from stars.services.starmap import generate_starmap, regenerate_all_starmaps


class Command(BaseCommand):
    help = 'Regenerate project starmap PNG previews.'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--project',
            dest='project_slug',
            help='Regenerate starmap for a single project slug.',
        )
        group.add_argument(
            '--all',
            action='store_true',
            help='Regenerate starmaps for all projects with stars.',
        )

    def handle(self, *args, **options):
        project_slug = options.get('project_slug')
        regenerate_all = options.get('all')

        if project_slug:
            project = Project.objects.get(slug=project_slug)
            result = generate_starmap(project)
            self.stdout.write(
                f'{project.slug}: stars={result.n_stars} '
                f'colored={result.colored_by_distance} preview={result.preview_url}',
            )
            return

        if regenerate_all:
            summary = regenerate_all_starmaps()
            self.stdout.write(
                f"Done: total={summary['total']} ok={summary['ok']} failed={summary['failed']}",
            )
            for error in summary['errors']:
                self.stdout.write(
                    self.style.ERROR(
                        f"{error['project_slug']}: {error['message']}",
                    ),
                )
            return

        self.stderr.write('Provide --project SLUG or --all.')
