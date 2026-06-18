from django.test import SimpleTestCase

from analysis.parameter_labels import (
    cname_display_label,
    parameter_display_name,
    parameter_label_with_unit,
    unit_display_name,
)


class ParameterLabelsTests(SimpleTestCase):
    def test_unit_display_solar_units(self):
        self.assertEqual(unit_display_name('solRad'), 'R☉')
        self.assertEqual(unit_display_name('solLum'), 'L☉')
        self.assertEqual(unit_display_name('Rsol'), 'R☉')
        self.assertEqual(unit_display_name('Msol'), 'M☉')

    def test_parameter_display_with_component(self):
        self.assertEqual(parameter_display_name('k', 1), 'Semiamplitude K₁')
        self.assertEqual(cname_display_label('k_2'), 'Semiamplitude K₂')

    def test_derived_parameter_display(self):
        self.assertEqual(cname_display_label('q'), 'Mass ratio q')
        self.assertEqual(
            cname_display_label('msini_1'),
            'Minimum mass M sin i₁',
        )

    def test_parameter_label_with_unit(self):
        self.assertEqual(
            parameter_label_with_unit('p', 'd'),
            'Orbital period P [d]',
        )
        self.assertEqual(
            parameter_label_with_unit('rad_1', 'solRad', from_cname=True),
            'Radius R₁ [R☉]',
        )

    def test_absolute_g_mag_label(self):
        self.assertEqual(
            parameter_label_with_unit('absolute_g_mag', 'mag', from_cname=True),
            'Absolute G-Band Magnitude [mag]',
        )

    def test_hrd_axis_labels_match_parameter_labels(self):
        from analysis.parameter_labels import hrd_axis_label, hrd_axis_labeldict

        self.assertEqual(
            hrd_axis_label('absolute_g_mag'),
            'Absolute G-Band Magnitude [mag]',
        )
        self.assertEqual(
            hrd_axis_label('mag_abs'),
            'Absolute G-Band Magnitude [mag]',
        )
        self.assertEqual(
            hrd_axis_labeldict()['bp_rp'],
            'BP-RP Color [mag]',
        )

    def test_mag_abs_alias_normalizes_to_absolute_g_mag(self):
        from analysis.parameter_labels import normalize_hrd_axis_key, normalize_parameter_name

        self.assertEqual(normalize_parameter_name('mag_abs'), 'absolute_g_mag')
        self.assertEqual(normalize_parameter_name('M_G'), 'absolute_g_mag')
        self.assertEqual(normalize_hrd_axis_key('mag_abs'), 'absolute_g_mag')
        self.assertEqual(normalize_hrd_axis_key('M_G'), 'absolute_g_mag')

    def test_stored_parameter_lookup_names(self):
        from analysis.parameter_aliases import stored_parameter_lookup_names

        self.assertEqual(
            stored_parameter_lookup_names('absolute_g_mag'),
            ['absolute_g_mag', 'mag_abs', 'M_G'],
        )

    def test_log_g_alias_normalizes_to_logg(self):
        from analysis.parameter_labels import normalize_parameter_name

        self.assertEqual(normalize_parameter_name('log_g'), 'logg')
        self.assertEqual(
            parameter_display_name('log_g'),
            parameter_display_name('logg'),
        )

    def test_met_alias_normalizes_to_z(self):
        from analysis.parameter_labels import normalize_parameter_name

        self.assertEqual(normalize_parameter_name('met'), 'z')
        self.assertEqual(
            parameter_display_name('met'),
            parameter_display_name('z'),
        )

    def test_vmicro_vrot_dilution_labels_with_units(self):
        self.assertEqual(
            parameter_label_with_unit('vmicro_1', 'km/s', from_cname=True),
            'Microturbulent velocity v_micro₁ [km/s]',
        )
        self.assertEqual(
            parameter_label_with_unit('vrot', 'km/s'),
            'Rotational velocity v sin i [km/s]',
        )
        self.assertEqual(
            parameter_label_with_unit('dilution_2', '', from_cname=True),
            'Light dilution factor₂',
        )

    def test_unknown_parameter_falls_back_to_name(self):
        self.assertEqual(parameter_display_name('custom_param'), 'custom_param')
