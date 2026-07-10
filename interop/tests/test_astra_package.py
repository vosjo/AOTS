import json
import struct
import zlib

from django.test import TestCase

from interop.astra_package import read_astra_package, write_astra_package
from interop.blob_pool import BlobPool


class AstraPackageTests(TestCase):
    def test_roundtrip_minimal_star(self):
        bp = BlobPool()
        stars = [{
            'id': 'star-1',
            'alias': 'Test Star',
            'ra': 10.0,
            'dec': 20.0,
            'spectra': [{
                'id': 'sp-1',
                'instrument': 'TEST',
                'b_wl': bp.add_doubles([4000.0, 4010.0]),
                'b_flux': bp.add_doubles([1.0, 1.1]),
                'fits': [],
            }],
        }]
        raw = write_astra_package(stars, blob_pool=bp)
        pkg = read_astra_package(raw)
        self.assertEqual(pkg.manifest['format'], 'astra-package')
        self.assertEqual(len(pkg.stars), 1)
        reader = pkg.blob_reader()
        wl = reader.get_doubles(pkg.stars[0]['spectra'][0]['b_wl'])
        self.assertEqual(wl, [4000.0, 4010.0])

    def test_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            read_astra_package(b'NOTASTRA')
