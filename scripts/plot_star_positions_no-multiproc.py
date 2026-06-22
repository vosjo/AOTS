#!/usr/bin/env python
"""Regenerate project starmap PNGs for all projects (single-process alias)."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')

import django

django.setup()

from stars.models import Project
from stars.services.starmap import generate_starmap


def main():
    for project in Project.objects.all().order_by('pk'):
        if not project.star_set.exists():
            continue
        print(project)
        result = generate_starmap(project)
        print(
            f'  stars={result.n_stars} colored={result.colored_by_distance} '
            f'preview={result.preview_url}',
        )


if __name__ == '__main__':
    main()
