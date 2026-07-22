"""
Migrate legacy media files to opaque UUID filenames and set original_name.

Idempotent: skips files that already look like UUID names under the new layout.
Writes a mapping log (old -> new) for rollback.
"""

from __future__ import annotations

import os
import re
import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from analysis.models import Analysis
from observations.models import LightCurve, RawSpecFile, SpecFile
from stars.models import Project
from users.models import User

UUID_NAME_RE = re.compile(r'^[0-9a-f]{32}(\.[A-Za-z0-9]+)?$')


def _is_already_opaque(relative: str, expected_prefix: str) -> bool:
    if not relative.startswith(expected_prefix.rstrip('/') + '/'):
        return False
    return bool(UUID_NAME_RE.match(Path(relative).name))


def _new_relative(subdir: str, old_name: str) -> str:
    ext = Path(old_name).suffix.lower()
    ext = ''.join(c for c in ext if c.isalnum() or c == '.')[:20]
    return f'{subdir}/{uuid.uuid4().hex}{ext}'


class Command(BaseCommand):
    help = 'Rename private/public media files to opaque UUID paths and fill original_name.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print actions without writing')
        parser.add_argument(
            '--mapping-log',
            default='media_uuid_migration.log',
            help='Path (relative to MEDIA_ROOT or absolute) for old->new mapping log',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        mapping_path = Path(options['mapping_log'])
        if not mapping_path.is_absolute():
            mapping_path = Path(settings.MEDIA_ROOT) / mapping_path

        media_root = Path(settings.MEDIA_ROOT)
        lines = []
        moved = 0

        jobs = [
            (SpecFile, 'specfile', 'spectra', 'original_name'),
            (RawSpecFile, 'rawfile', 'raw_spectra', 'original_name'),
            (LightCurve, 'lcfile', 'lightcurves', 'original_name'),
            (Analysis, 'datafile', 'analyses', 'original_name'),
            (Project, 'logo', 'public/projects', None),
            (User, 'profile_picture', 'public/profile_pictures', None),
        ]

        for model, field_name, subdir, original_attr in jobs:
            for obj in model.objects.all().iterator():
                field = getattr(obj, field_name)
                if not field or not field.name:
                    continue
                old_rel = field.name
                old_abs = media_root / old_rel

                if original_attr and not getattr(obj, original_attr, ''):
                    setattr(obj, original_attr, Path(old_rel).name)

                if _is_already_opaque(old_rel, subdir):
                    if original_attr and not dry_run:
                        obj.save(update_fields=[original_attr])
                    continue

                new_rel = _new_relative(subdir, old_rel)
                new_abs = media_root / new_rel
                lines.append(f'{old_rel}\t{new_rel}\t{model.__name__}\t{obj.pk}')

                if dry_run:
                    self.stdout.write(f'WOULD MOVE {old_rel} -> {new_rel}')
                    moved += 1
                    continue

                if not old_abs.is_file():
                    self.stderr.write(self.style.WARNING(f'Missing file, DB only update: {old_rel}'))
                    getattr(obj, field_name).name = new_rel
                    update_fields = [field_name]
                    if original_attr:
                        update_fields.append(original_attr)
                    with transaction.atomic():
                        obj.save(update_fields=update_fields)
                    moved += 1
                    continue

                new_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_abs), str(new_abs))
                getattr(obj, field_name).name = new_rel
                update_fields = [field_name]
                if original_attr:
                    update_fields.append(original_attr)
                with transaction.atomic():
                    obj.save(update_fields=update_fields)
                moved += 1
                self.stdout.write(f'MOVED {old_rel} -> {new_rel}')

        if not dry_run and lines:
            mapping_path.parent.mkdir(parents=True, exist_ok=True)
            with mapping_path.open('a', encoding='utf-8') as fh:
                for line in lines:
                    fh.write(line + '\n')
            self.stdout.write(self.style.SUCCESS(f'Wrote mapping log: {mapping_path}'))

        self.stdout.write(self.style.SUCCESS(f'Done. {moved} file(s) processed (dry_run={dry_run}).'))
