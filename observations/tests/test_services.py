from unittest.mock import MagicMock, patch

from django.test import TestCase

from observations.services import fits_io


class FitsIoServiceTests(TestCase):
    @patch('observations.services.fits_io.fits.getheader')
    def test_read_specfile_header_returns_dict(self, mock_getheader):
        mock_getheader.return_value = {'TELESCOP': 'Test', 'comment': 'skip'}
        specfile = MagicMock()
        specfile.specfile.path = '/tmp/test.fits'
        header = fits_io.read_specfile_header(specfile)
        self.assertEqual(header['TELESCOP'], 'Test')
        self.assertNotIn('comment', header)
