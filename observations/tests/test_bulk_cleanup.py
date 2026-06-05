import os
import time
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.test import TestCase, override_settings

from observations.services.bulk_download import (
    bulk_download_artifact_path,
    bulk_download_filename,
    cleanup_expired_bulk_downloads,
)


class BulkDownloadFilenameTests(TestCase):
    def test_bulk_download_filename_uses_kind_and_timestamp(self):
        moment = datetime(2026, 5, 23, 14, 30, 52, tzinfo=dt_timezone.utc)
        self.assertEqual(
            bulk_download_filename('processed', at=moment),
            'spectra_20260523_143052.zip',
        )
        self.assertEqual(
            bulk_download_filename('lightcurves', at=moment),
            'lightcurves_20260523_143052.zip',
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
