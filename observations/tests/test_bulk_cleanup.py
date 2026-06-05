import os
import time

from django.conf import settings
from django.test import TestCase, override_settings

from observations.services.bulk_download import (
    bulk_download_artifact_path,
    cleanup_expired_bulk_downloads,
)


class BulkDownloadCleanupTests(TestCase):
    @override_settings(BULK_DOWNLOAD_TTL_SECONDS=60)
    def test_cleanup_removes_old_zip(self):
        path = bulk_download_artifact_path('test-cleanup-task')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(b'zip')

        old_time = time.time() - 120
        os.utime(path, (old_time, old_time))

        removed = cleanup_expired_bulk_downloads()
        self.assertGreaterEqual(removed, 1)
        self.assertFalse(os.path.isfile(path))
