from django.test import SimpleTestCase

from interop.filenames import sanitize_astra_filename


class AstraFilenameTests(SimpleTestCase):
    def test_star_name(self):
        self.assertEqual(sanitize_astra_filename('HD 12345'), 'HD_12345.astra')

    def test_already_has_suffix(self):
        self.assertEqual(sanitize_astra_filename('foo.astra'), 'foo.astra')

    def test_empty_uses_default(self):
        self.assertEqual(sanitize_astra_filename('', default='fallback.astra'), 'fallback.astra')
