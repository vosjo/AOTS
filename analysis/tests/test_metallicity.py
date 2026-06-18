from django.test import SimpleTestCase

from analysis.auxil.read_analyses import parameter_homogenisation
from analysis.models.default_values import DEFAULT_PARAMETERS
from analysis.parameter_labels import parameter_display_name, parameter_label_with_unit
from analysis.services.metallicity import metallicity_to_feh_dex
from analysis.services.parameter_names import resolve_ingest_parameter_name


class MetallicityConversionTests(SimpleTestCase):
    def test_feh_dex_passthrough(self):
        value, err_l, err_u, unit = metallicity_to_feh_dex(-0.5, 0.1, 0.1, unit='dex')
        self.assertEqual(unit, 'dex')
        self.assertAlmostEqual(value, -0.5)
        self.assertAlmostEqual(err_l, 0.1)

    def test_mass_fraction_converts_to_feh_dex(self):
        value, err_l, err_u, unit = metallicity_to_feh_dex(
            0.0122, 0.001, 0.001, unit='Zsun',
        )
        self.assertEqual(unit, 'dex')
        self.assertAlmostEqual(value, 0.0, places=2)
        self.assertGreater(err_l, 0.0)
        self.assertGreater(err_u, 0.0)


class ParameterHomogenisationTests(SimpleTestCase):
    def test_met_alias_stored_as_z_in_dex(self):
        result = parameter_homogenisation({
            'met1': {'value': -0.3, 'err_l': 0.05, 'err_u': 0.05, 'unit': 'dex'},
        })
        self.assertIn('z1', result)
        self.assertEqual(result['z1'][3], 'dex')
        self.assertAlmostEqual(result['z1'][0], -0.3)

    def test_mass_fraction_met_converted(self):
        result = parameter_homogenisation({
            'met': {'value': 0.0122, 'err_l': 0.001, 'err_u': 0.001, 'unit': 'Zsun'},
        })
        self.assertIn('z', result)
        self.assertEqual(result['z'][3], 'dex')
        self.assertAlmostEqual(result['z'][0], 0.0, places=2)

    def test_component_suffix_teff1(self):
        result = parameter_homogenisation({
            'teff1': {'value': 6000.0, 'err_l': 100.0, 'err_u': 100.0, 'unit': 'K'},
        })
        self.assertIn('teff1', result)
        self.assertEqual(result['teff1'][3], 'K')

    def test_list_input_format(self):
        result = parameter_homogenisation({
            'z2': [-0.1, 0.02, 0.02, 'dex'],
        })
        self.assertIn('z2', result)
        self.assertAlmostEqual(result['z2'][0], -0.1)

    def test_vmicro_empty_unit_stored_as_km_s(self):
        result = parameter_homogenisation({
            'vmicro1': {'value': 2.0, 'err_l': 0.5, 'err_u': 0.5, 'unit': ''},
        })
        self.assertIn('vmicro1', result)
        self.assertEqual(result['vmicro1'][3], 'km/s')
        self.assertAlmostEqual(result['vmicro1'][0], 2.0)

    def test_vrot_with_explicit_unit(self):
        result = parameter_homogenisation({
            'vrot2': {'value': 15.0, 'err_l': 3.0, 'err_u': 3.0, 'unit': 'km/s'},
        })
        self.assertIn('vrot2', result)
        self.assertEqual(result['vrot2'][3], 'km/s')
        self.assertAlmostEqual(result['vrot2'][0], 15.0)

    def test_dilution_dimensionless(self):
        result = parameter_homogenisation({
            'dilution1': {'value': 0.85, 'err_l': 0.05, 'err_u': 0.05, 'unit': ''},
        })
        self.assertIn('dilution1', result)
        self.assertEqual(result['dilution1'][3], '')
        self.assertAlmostEqual(result['dilution1'][0], 0.85)


class ParameterNameTests(SimpleTestCase):
    def test_met_resolves_to_z(self):
        self.assertEqual(resolve_ingest_parameter_name('met'), ('z', 0))
        self.assertEqual(resolve_ingest_parameter_name('met2'), ('z', 2))

    def test_z_in_default_parameters(self):
        self.assertEqual(DEFAULT_PARAMETERS['z'], 'dex')

    def test_vmicro_vrot_dilution_in_default_parameters(self):
        self.assertEqual(DEFAULT_PARAMETERS['vmicro'], 'km/s')
        self.assertEqual(DEFAULT_PARAMETERS['vrot'], 'km/s')
        self.assertEqual(DEFAULT_PARAMETERS['dilution'], '')

    def test_met_display_uses_z_label(self):
        self.assertEqual(
            parameter_display_name('met'),
            parameter_display_name('z'),
        )
        self.assertEqual(
            parameter_label_with_unit('met', 'dex', from_cname=True),
            parameter_label_with_unit('z', 'dex', from_cname=True),
        )
