import numpy as np
from django.test import TestCase

from analysis.models import Parameter, ParameterConsensusPolicy, ParameterSource
from analysis.models.consensus_policy import ConsensusRuleKind
from analysis.services import parameter_io
from analysis.services.consensus_defaults import seed_project_consensus_policies
from analysis.services.parameter_consensus import (
    get_consensus_parameter,
    get_policy,
    list_other_measurements,
    refresh_project_consensus,
    resolve_consensus,
    sync_consensus_cache,
)
from stars.models import Project, Star


class ParameterConsensusTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Consensus', description='')
        self.star = Star.objects.create(
            name='Vega',
            project=self.project,
            ra=279.23,
            dec=38.78,
        )
        self.dr2 = ParameterSource.objects.create(name='Gaia DR2', project=self.project)
        self.dr3 = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        seed_project_consensus_policies(self.project)

    def test_default_policies_seeded_for_new_project(self):
        self.assertTrue(
            ParameterConsensusPolicy.objects.filter(
                project=self.project,
                name='parallax',
                rule=ConsensusRuleKind.SOURCE_PRIORITY,
            ).exists(),
        )
        self.assertTrue(
            ParameterConsensusPolicy.objects.filter(
                project=self.project,
                name='*',
                rule=ConsensusRuleKind.WEIGHTED_AVERAGE,
            ).exists(),
        )

    def test_weighted_average_single_source_uses_source_provenance(self):
        src = ParameterSource.objects.create(name='Gaia DR3', project=self.project)
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=5.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=src,
        )
        sync_consensus_cache(self.star, 'parallax', 0)
        p = get_consensus_parameter(self.star, 'parallax', 0)
        self.assertAlmostEqual(p.value, 5.0)
        self.assertEqual(p.consensus_provenance, 'Gaia DR3')
        self.assertEqual(p.consensus_from_id, Parameter.objects.get(parameter_source=src).pk)

    def test_weighted_average_uses_inverse_variance(self):
        parameter_io.create_measurement(
            star=self.star,
            name='teff',
            component=1,
            value=30000,
            error_l=5000,
            error_u=5000,
            unit='K',
            parameter_source=ParameterSource.objects.create(name='src1', project=self.project),
        )
        parameter_io.create_measurement(
            star=self.star,
            name='teff',
            component=1,
            value=35000,
            error_l=3000,
            error_u=3000,
            unit='K',
            parameter_source=ParameterSource.objects.create(name='src2', project=self.project),
        )
        p = get_consensus_parameter(self.star, 'teff', 1)
        self.assertIsNotNone(p)
        self.assertEqual(np.round(p.value, 0), 33676)
        self.assertAlmostEqual(p.error, 2572.5, delta=0.1)
        self.assertEqual(p.consensus_rule, ConsensusRuleKind.WEIGHTED_AVERAGE)
        self.assertIn('Weighted avg', p.consensus_provenance)

    def test_weighted_average_lists_all_sources_as_other_measurements(self):
        parameter_io.create_measurement(
            star=self.star,
            name='teff',
            component=1,
            value=30000,
            error_l=5000,
            error_u=5000,
            unit='K',
            parameter_source=ParameterSource.objects.create(name='src1', project=self.project),
        )
        parameter_io.create_measurement(
            star=self.star,
            name='teff',
            component=1,
            value=35000,
            error_l=3000,
            error_u=3000,
            unit='K',
            parameter_source=ParameterSource.objects.create(name='src2', project=self.project),
        )
        others = list_other_measurements(self.star, 'teff', 1)
        self.assertEqual(len(others), 2)
        self.assertEqual({p.value for p in others}, {30000.0, 35000.0})

    def test_preferred_source_hides_winner_from_other_measurements(self):
        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='parallax',
            component=0,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
            },
        )
        dr2_param = parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=10.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr2,
        )
        dr3_param = parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=11.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        sync_consensus_cache(self.star, 'parallax', 0)
        others = list_other_measurements(self.star, 'parallax', 0)
        self.assertEqual(len(others), 1)
        self.assertEqual(others[0].pk, dr2_param.pk)
        self.assertNotIn(dr3_param.pk, [p.pk for p in others])

    def test_single_measurement_has_no_other_measurements(self):
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=5.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        sync_consensus_cache(self.star, 'parallax', 0)
        self.assertEqual(list_other_measurements(self.star, 'parallax', 0), [])

    def test_get_params_includes_other_measurements(self):
        from stars.auxil import get_params

        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=10.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr2,
        )
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=11.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        refresh_project_consensus(self.project)
        overview = get_params(self.star.pk)
        system_rows = overview[0]['params']
        parallax = next(row for row in system_rows if row['pinfo'].name == 'parallax')
        self.assertEqual(len(parallax['other_measurements']), 1)
        self.assertEqual(parallax['other_measurements'][0]['provenance'], 'Gaia DR2')

    def test_preferred_source_dr3_over_dr2(self):
        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='parallax',
            component=0,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
                'fallback_rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'fallback_preferred_source': self.dr2,
            },
        )
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=10.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr2,
        )
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=11.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        sync_consensus_cache(self.star, 'parallax', 0)
        p = get_consensus_parameter(self.star, 'parallax', 0)
        self.assertAlmostEqual(p.value, 11.0)
        self.assertEqual(p.consensus_provenance, 'Gaia DR3')
        self.assertEqual(p.consensus_from_id, Parameter.objects.get(parameter_source=self.dr3).pk)

    def test_preferred_source_fallback_to_dr2(self):
        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='parallax',
            component=0,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
                'fallback_rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'fallback_preferred_source': self.dr2,
            },
        )
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=9.5,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr2,
        )
        sync_consensus_cache(self.star, 'parallax', 0)
        p = get_consensus_parameter(self.star, 'parallax', 0)
        self.assertAlmostEqual(p.value, 9.5)
        self.assertEqual(p.consensus_provenance, 'Gaia DR2')

    def test_policy_resolution_specific_over_wildcard(self):
        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='parallax',
            component=0,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
            },
        )
        policy = get_policy(self.project, 'parallax', 0)
        self.assertEqual(policy.rule, ConsensusRuleKind.PREFERRED_SOURCE)
        pmra_policy = get_policy(self.project, 'pmra', 0)
        self.assertEqual(pmra_policy.rule, ConsensusRuleKind.SOURCE_PRIORITY)
        wildcard = get_policy(self.project, 'custom_param', 0)
        self.assertEqual(wildcard.name, '*')

    def test_refresh_project_consensus_after_policy_change(self):
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=8.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr2,
        )
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=9.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        refresh_project_consensus(self.project)
        p = get_consensus_parameter(self.star, 'parallax', 0)
        self.assertAlmostEqual(p.value, 9.0)

        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='parallax',
            component=0,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
            },
        )
        refresh_project_consensus(self.project)
        p = get_consensus_parameter(self.star, 'parallax', 0)
        self.assertAlmostEqual(p.value, 9.0)
        self.assertEqual(p.consensus_provenance, 'Gaia DR3')

    def test_resolve_consensus_preview(self):
        parameter_io.create_measurement(
            star=self.star,
            name='parallax',
            value=5.0,
            error_l=0.1,
            error_u=0.1,
            unit='mas',
            parameter_source=self.dr3,
        )
        result = resolve_consensus(self.star, 'parallax', 0)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.value, 5.0)

    def test_legacy_policy_name_with_suffix_resolves_by_component(self):
        from analysis.models.default_values import PRIMARY
        from analysis.services.parameter_names import normalize_policy_parameter

        ParameterConsensusPolicy.objects.update_or_create(
            project=self.project,
            name='k',
            component=PRIMARY,
            defaults={
                'rule': ConsensusRuleKind.PREFERRED_SOURCE,
                'preferred_source': self.dr3,
            },
        )
        name, component = normalize_policy_parameter('k1', 0)
        self.assertEqual(name, 'k')
        self.assertEqual(component, PRIMARY)
        policy = get_policy(self.project, 'k', PRIMARY)
        self.assertIsNotNone(policy)
        self.assertEqual(policy.preferred_source_id, self.dr3.pk)
