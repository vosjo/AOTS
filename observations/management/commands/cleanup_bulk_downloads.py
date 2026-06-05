from django.core.management.base import BaseCommand

from observations.services.bulk_download import cleanup_expired_bulk_downloads


class Command(BaseCommand):
    help = 'Delete bulk-download ZIP files older than BULK_DOWNLOAD_TTL_SECONDS.'

    def handle(self, *args, **options):
        removed = cleanup_expired_bulk_downloads()
        self.stdout.write(self.style.SUCCESS(f'Removed {removed} expired bulk download file(s).'))
