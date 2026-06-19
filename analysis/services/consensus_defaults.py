"""Default parameter consensus policies seeded for each project."""

from __future__ import annotations

from analysis.categories import AnalysisCategory
from analysis.models.consensus_policy import CONSENSUS_WILDCARD, ConsensusRuleKind
from analysis.models.default_values import PRIMARY, SECONDARY, SYSTEM

GAIA_SOURCE_PRIORITY = ['Gaia DR3', 'Gaia DR2']

# Catalog astrometry / photometry (names match ParameterSource rows from Gaia import scripts).
CATALOG_ASTROMETRY_PARAMETERS = (
    'parallax',
    'pmra',
    'pmdec',
    'mag',
    'absolute_g_mag',
    'bp_rp',
)

# Binary/system parameters from RV solutions.
RV_SYSTEM_PARAMETERS = ('p', 't0', 'e', 'omega', 'v0')

# Component-specific RV semiamplitudes.
RV_COMPONENT_PARAMETERS = ('k',)

# Stellar parameters from spectral analyses.
SPECTRAL_PARAMETERS = ('teff', 'logg', 'rad', 'z', 'vmicro', 'vrot', 'dilution')

# SED / photometric fit parameters.
SED_PARAMETERS = ('ebv', 'L', 'd')


def _source_priority_template(name: str, *, component: int = SYSTEM) -> dict:
    return {
        'name': name,
        'component': component,
        'rule': ConsensusRuleKind.SOURCE_PRIORITY,
        'source_priority': list(GAIA_SOURCE_PRIORITY),
        'fallback_rule': ConsensusRuleKind.WEIGHTED_AVERAGE,
    }


def _analysis_category_template(
    name: str,
    category: str,
    *,
    component: int = SYSTEM,
) -> dict:
    return {
        'name': name,
        'component': component,
        'rule': ConsensusRuleKind.PREFERRED_ANALYSIS_CATEGORY,
        'preferred_analysis_category': category,
        'fallback_rule': ConsensusRuleKind.WEIGHTED_AVERAGE,
    }


def iter_default_consensus_policy_templates() -> list[dict]:
    """Policy rows applied to every new project (and backfilled by migration)."""
    templates: list[dict] = []

    for name in CATALOG_ASTROMETRY_PARAMETERS:
        templates.append(_source_priority_template(name))

    for name in RV_SYSTEM_PARAMETERS:
        templates.append(_analysis_category_template(name, AnalysisCategory.RV_SOLUTION))

    for component in (PRIMARY, SECONDARY):
        for name in RV_COMPONENT_PARAMETERS:
            templates.append(
                _analysis_category_template(name, AnalysisCategory.RV_SOLUTION, component=component),
            )

    for name in SPECTRAL_PARAMETERS:
        templates.append(_analysis_category_template(name, AnalysisCategory.SPECTRAL_FIT))

    for name in SED_PARAMETERS:
        templates.append(_analysis_category_template(name, AnalysisCategory.SED_FIT))

    templates.append({
        'name': CONSENSUS_WILDCARD,
        'component': SYSTEM,
        'rule': ConsensusRuleKind.WEIGHTED_AVERAGE,
    })
    return templates


def seed_project_consensus_policies(project, *, policy_model=None) -> int:
    """
    Create missing default policies for ``project``.

    Existing rows (same name + component) are left unchanged.
    Returns the number of policies created.
    """
    from analysis.models.consensus_policy import ParameterConsensusPolicy

    Policy = policy_model or ParameterConsensusPolicy
    created = 0
    for template in iter_default_consensus_policy_templates():
        name = template['name']
        component = template['component']
        defaults = {
            key: value
            for key, value in template.items()
            if key not in ('name', 'component')
        }
        _, was_created = Policy.objects.get_or_create(
            project=project,
            name=name,
            component=component,
            defaults=defaults,
        )
        if was_created:
            created += 1
    return created
