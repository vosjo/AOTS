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
        self.assertEqual(cname_display_label('q'), 'Mass ratio (q)')
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

    def test_omega_label_with_degrees(self):
        self.assertEqual(
            parameter_label_with_unit('omega', 'deg'),
            'Argument of periastron ω [°]',
        )
        self.assertEqual(unit_display_name('deg'), '°')

    def test_t0_epoch_alias_and_labels(self):
        from analysis.parameter_labels import (
            PLOTTER_GROUP_ORBIT,
            normalize_parameter_name,
            plotter_parameter_group,
        )

        self.assertEqual(normalize_parameter_name('t0'), 't0')
        self.assertEqual(normalize_parameter_name('t'), 't0')
        self.assertEqual(
            parameter_label_with_unit('t0', 'd'),
            'Epoch T₀ [d]',
        )
        self.assertEqual(
            parameter_label_with_unit('t', 'd'),
            'Epoch T₀ [d]',
        )
        self.assertEqual(cname_display_label('t'), 'Epoch T₀')
        self.assertEqual(plotter_parameter_group('t0'), PLOTTER_GROUP_ORBIT)
        self.assertEqual(plotter_parameter_group('t'), PLOTTER_GROUP_ORBIT)

    def test_consensus_parameter_grouping(self):
        from analysis.parameter_labels import (
            PLOTTER_GROUP_ASTROMETRY,
            PLOTTER_GROUP_ORBIT,
            PLOTTER_GROUP_STELLAR,
            group_consensus_parameter_choices,
            serialize_plotter_choices,
        )

        grouped = group_consensus_parameter_choices([
            ('*', 'All parameters (*)'),
            ('teff', 'Effective temperature T_eff [K]'),
            ('p', 'Orbital period P [d]'),
            ('parallax', 'Parallax'),
            ('t0', 'Epoch T₀ [d]'),
        ])
        self.assertEqual(grouped[0], ('*', 'All parameters (*)'))
        self.assertEqual(grouped[1][0], PLOTTER_GROUP_ASTROMETRY)
        self.assertEqual(grouped[2][0], PLOTTER_GROUP_ORBIT)
        self.assertEqual(grouped[3][0], PLOTTER_GROUP_STELLAR)

        serialized = serialize_plotter_choices(grouped)
        self.assertEqual(serialized[0]['value'], '*')
        self.assertEqual(serialized[1]['group'], PLOTTER_GROUP_ASTROMETRY)
        self.assertEqual(serialized[2]['group'], PLOTTER_GROUP_ORBIT)

    def test_plotter_parameter_grouping(self):
        from analysis.parameter_labels import (
            PLOTTER_GROUP_ASTROMETRY,
            PLOTTER_GROUP_ORBIT,
            PLOTTER_GROUP_STELLAR,
            group_plotter_parameter_choices,
            plotter_parameter_group,
            serialize_plotter_choices,
        )

        self.assertEqual(plotter_parameter_group('p'), PLOTTER_GROUP_ORBIT)
        self.assertEqual(plotter_parameter_group('k_1'), PLOTTER_GROUP_ORBIT)
        self.assertEqual(plotter_parameter_group('teff_1'), PLOTTER_GROUP_STELLAR)
        self.assertEqual(plotter_parameter_group('parallax'), PLOTTER_GROUP_ASTROMETRY)
        self.assertEqual(plotter_parameter_group('pmra'), PLOTTER_GROUP_ASTROMETRY)
        self.assertEqual(plotter_parameter_group('d'), PLOTTER_GROUP_ASTROMETRY)

        grouped = group_plotter_parameter_choices([
            ('teff_1', 'Effective temperature T_eff₁ [K]'),
            ('p', 'Orbital period P [d]'),
            ('parallax', 'Parallax'),
        ])
        self.assertEqual(grouped[0][0], PLOTTER_GROUP_ASTROMETRY)
        self.assertEqual(grouped[1][0], PLOTTER_GROUP_ORBIT)
        self.assertEqual(grouped[2][0], PLOTTER_GROUP_STELLAR)
        serialized = serialize_plotter_choices(grouped)
        self.assertEqual(serialized[1]['group'], PLOTTER_GROUP_ORBIT)
        self.assertEqual(serialized[1]['options'][0]['value'], 'p')
