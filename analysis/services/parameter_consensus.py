"""Project consensus resolution for star parameters."""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from analysis.models.consensus_policy import (
    CONSENSUS_WILDCARD,
    ConsensusRuleKind,
    ParameterConsensusPolicy,
)
from analysis.models.default_values import SYSTEM, split_parameter_name
from analysis.models.parameter_source import ParameterSourceKind
from analysis.parameter_aliases import stored_parameter_lookup_names
from analysis.parameter_labels import normalize_parameter_name
from analysis.services.parameter_averaging import calculate_average
from analysis.services.parameter_names import storage_parameter_name
from analysis.services.parameter_sources import get_or_create_avg_source


@dataclass
class ConsensusResult:
    value: float
    error_l: float
    error_u: float
    unit: str
    rule: str
    provenance_label: str
    source_parameter_id: int | None
    candidate_count: int


def _lookup_names(name: str) -> list[str]:
    if name == 'absolute_g_mag':
        return stored_parameter_lookup_names(name)
    return [name]


def _filter_by_name(qs, name: str):
    if name == 'absolute_g_mag':
        return qs.filter(name__in=_lookup_names(name))
    return qs.filter(name__iexact=name)


def _non_derived_consensus_qs(qs):
    """Exclude DerivedParameter rows from a consensus queryset."""
    return qs.filter(derivedparameter__isnull=True)


def _policy_lookup_keys(name: str, component: int) -> list[tuple[str, int]]:
    """Candidate (name, component) pairs for policy lookup, most specific first."""
    if name == '*':
        return [(CONSENSUS_WILDCARD, SYSTEM)]

    canonical = normalize_parameter_name(name)
    keys: list[tuple[str, int]] = [(canonical, component)]
    if component != SYSTEM:
        keys.append((canonical, SYSTEM))
    if component in (1, 2):
        keys.append((storage_parameter_name(canonical, component), SYSTEM))
    _, suffix_component = split_parameter_name(name)
    if suffix_component in (1, 2) and name not in {canonical, storage_parameter_name(canonical, suffix_component)}:
        keys.append((name, SYSTEM))
    keys.append((CONSENSUS_WILDCARD, SYSTEM))

    seen: set[tuple[str, int]] = set()
    unique: list[tuple[str, int]] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def get_policy(project, name: str, component: int) -> ParameterConsensusPolicy | None:
    """Most specific policy: exact (name, component) > (name, SYSTEM) > wildcard."""
    lookup_name = normalize_parameter_name(name) if name != '*' else name
    for policy_name, policy_component in _policy_lookup_keys(lookup_name, component):
        try:
            return ParameterConsensusPolicy.objects.get(
                project=project,
                name=policy_name,
                component=policy_component,
            )
        except ParameterConsensusPolicy.DoesNotExist:
            continue
    return None


def list_measurement_candidates(star, name: str, component: int):
    """Valid non-consensus measurements from analyses or catalog sources."""
    from analysis.models.parameters import Parameter

    qs = Parameter.objects.filter(
        star=star,
        component=component,
        valid=True,
        average=False,
    )
    qs = _filter_by_name(qs, name)
    return qs.filter(
        Q(analysis__isnull=False)
        | Q(parameter_source__kind=ParameterSourceKind.CATALOG),
    )


def list_catalog_measurement_candidates(star, name: str, component: int):
    """Valid catalog-source measurements only (excludes analysis parameters)."""
    from analysis.models.parameters import Parameter

    qs = Parameter.objects.filter(
        star=star,
        component=component,
        valid=True,
        average=False,
        parameter_source__kind=ParameterSourceKind.CATALOG,
    )
    return _filter_by_name(qs, name)


def consensus_queryset(*, star=None, project=None):
    """Consensus cache rows (``average=True``); use instead of filtering in application code."""
    from analysis.models.parameters import Parameter

    qs = Parameter.objects.filter(average=True, valid=True)
    if star is not None:
        qs = qs.filter(star=star)
    if project is not None:
        qs = qs.filter(star__project=project)
    return qs


def iter_project_consensus_cnames(project):
    """Distinct (cname, unit) pairs for plotter axis choices."""
    return (
        _non_derived_consensus_qs(consensus_queryset(project=project))
        .values_list('cname', 'unit')
        .distinct()
        .order_by('cname')
    )


def get_consensus_parameter(star, name: str, component: int = SYSTEM):
    """Cached consensus row for a star parameter, if present."""
    qs = _non_derived_consensus_qs(consensus_queryset(star=star)).filter(component=component)
    qs = _filter_by_name(qs, name)
    return qs.first()


def _is_single_source_weighted_avg_label(label: str) -> bool:
    return label.startswith('Weighted avg (1 source')


def consensus_provenance_display(star, param, name: str, component: int = SYSTEM) -> str:
    """Human-readable provenance for a consensus cache row (backfills stale cache if needed)."""
    if param is None:
        return ''
    label = param.consensus_provenance
    if label and not _is_single_source_weighted_avg_label(label):
        return label
    result = resolve_consensus(star, name, component)
    if result is None or not result.provenance_label:
        return label or ''
    if (
        label != result.provenance_label
        or param.consensus_rule != result.rule
        or param.consensus_from_id != result.source_parameter_id
    ):
        param.consensus_rule = result.rule
        param.consensus_provenance = result.provenance_label
        param.consensus_from_id = result.source_parameter_id
        param.save(update_fields=['consensus_rule', 'consensus_provenance', 'consensus_from'])
    return result.provenance_label


def get_consensus_result(star, name: str, component: int = SYSTEM) -> ConsensusResult | None:
    """Resolve consensus without requiring a warm cache (useful for previews)."""
    return resolve_consensus(star, name, component)


def _provenance_label(param) -> str:
    if param.analysis_id:
        try:
            from analysis.categories import category_label
            return category_label(param.analysis.category)
        except Exception:
            return 'Analysis'
    if param.parameter_source_id:
        return param.parameter_source.name
    return 'Measurement'


def _result_from_winner(winner, rule: str, candidate_count: int) -> ConsensusResult:
    return ConsensusResult(
        value=winner.value,
        error_l=winner.error_l,
        error_u=winner.error_u,
        unit=winner.unit,
        rule=rule,
        provenance_label=_provenance_label(winner),
        source_parameter_id=winner.pk,
        candidate_count=candidate_count,
    )


def _result_from_average(candidates, rule: str) -> ConsensusResult:
    count = candidates.count()
    if count == 1:
        return _result_from_winner(candidates.first(), rule, 1)
    value, error = calculate_average(candidates)
    unit = candidates.first().unit
    return ConsensusResult(
        value=value,
        error_l=error,
        error_u=error,
        unit=unit,
        rule=rule,
        provenance_label=f'Weighted avg ({count} sources)',
        source_parameter_id=None,
        candidate_count=count,
    )


def _apply_rule(
    candidates,
    rule: str,
    *,
    project,
    preferred_source=None,
    preferred_analysis_category: str = '',
    source_priority=None,
) -> ConsensusResult | None:
    if not candidates.exists():
        return None

    count = candidates.count()

    if rule == ConsensusRuleKind.PREFERRED_SOURCE:
        if preferred_source is not None:
            winner = candidates.filter(parameter_source_id=preferred_source.pk).first()
            if winner is not None:
                return _result_from_winner(winner, rule, count)

    elif rule == ConsensusRuleKind.PREFERRED_ANALYSIS_CATEGORY:
        if preferred_analysis_category:
            winner = candidates.filter(analysis__category=preferred_analysis_category).first()
            if winner is not None:
                return _result_from_winner(winner, rule, count)

    elif rule == ConsensusRuleKind.SOURCE_PRIORITY:
        for entry in source_priority or []:
            if isinstance(entry, int):
                winner = candidates.filter(parameter_source_id=entry).first()
            else:
                winner = candidates.filter(parameter_source__name=str(entry)).first()
            if winner is not None:
                return _result_from_winner(winner, rule, count)

    elif rule == ConsensusRuleKind.LATEST:
        winner = candidates.order_by('-pk').first()
        if winner is not None:
            return _result_from_winner(winner, rule, count)

    elif rule == ConsensusRuleKind.WEIGHTED_AVERAGE:
        return _result_from_average(candidates, rule)

    return None


def _resolve_with_policy(candidates, policy, project) -> ConsensusResult | None:
    if not candidates.exists():
        return None

    rule = policy.rule if policy else ConsensusRuleKind.WEIGHTED_AVERAGE
    result = _apply_rule(
        candidates,
        rule,
        project=project,
        preferred_source=policy.preferred_source if policy else None,
        preferred_analysis_category=policy.preferred_analysis_category if policy else '',
        source_priority=policy.source_priority if policy else [],
    )
    if result is not None:
        return result

    if policy and policy.fallback_rule:
        fallback = _apply_rule(
            candidates,
            policy.fallback_rule,
            project=project,
            preferred_source=policy.fallback_preferred_source,
            preferred_analysis_category=policy.fallback_analysis_category,
            source_priority=policy.source_priority,
        )
        if fallback is not None:
            return fallback

    if rule != ConsensusRuleKind.WEIGHTED_AVERAGE:
        return _result_from_average(candidates, ConsensusRuleKind.WEIGHTED_AVERAGE)
    return None


def resolve_consensus(star, name: str, component: int = SYSTEM) -> ConsensusResult | None:
    """Compute consensus for one star parameter from project policy."""
    policy = get_policy(star.project, name, component)
    candidates = list_measurement_candidates(star, name, component)
    return _resolve_with_policy(candidates, policy, star.project)


def resolve_catalog_consensus(star, name: str, component: int = SYSTEM) -> ConsensusResult | None:
    """Consensus from catalog ParameterSource measurements only."""
    policy = get_policy(star.project, name, component)
    candidates = list_catalog_measurement_candidates(star, name, component)
    return _resolve_with_policy(candidates, policy, star.project)


def _delete_consensus_cache(star, name: str, component: int) -> None:
    from analysis.services import parameter_io

    for param in _filter_by_name(
        _non_derived_consensus_qs(
            consensus_queryset(star=star).filter(component=component),
        ),
        name,
    ):
        parameter_io.delete_measurement(param, run_after=True)


def sync_consensus_cache(star, name: str, component: int):
    """Materialize consensus into the AVG cache row for this parameter."""
    from analysis.models.parameters import Parameter

    result = resolve_consensus(star, name, component)
    if result is None:
        _delete_consensus_cache(star, name, component)
        return None

    existing = _filter_by_name(
        _non_derived_consensus_qs(
            consensus_queryset(star=star).filter(component=component),
        ),
        name,
    )
    if existing.count() > 1:
        _delete_consensus_cache(star, name, component)
        existing = _filter_by_name(
            _non_derived_consensus_qs(
                consensus_queryset(star=star).filter(component=component),
            ),
            name,
        )

    try:
        ap = existing.get()
        ap.value = result.value
        ap.error_l = result.error_l
        ap.error_u = result.error_u
        ap.unit = result.unit
        ap.consensus_rule = result.rule
        ap.consensus_provenance = result.provenance_label
        ap.consensus_from_id = result.source_parameter_id
        ap.save()
    except Parameter.DoesNotExist:
        ds = get_or_create_avg_source(star.project)
        ap = Parameter.objects.create(
            star=star,
            name=name,
            component=component,
            value=result.value,
            error_l=result.error_l,
            error_u=result.error_u,
            unit=result.unit,
            average=True,
            valid=True,
            parameter_source=ds,
            consensus_rule=result.rule,
            consensus_provenance=result.provenance_label,
            consensus_from_id=result.source_parameter_id,
        )

    if ap.derived_parameters.exists():
        from analysis.services.parameter_derivation import refresh_derived_for
        refresh_derived_for(ap)
    return ap


def sync_consensus_for_star(star) -> None:
    """Refresh all consensus cache rows for one star."""
    from analysis.models.parameters import Parameter

    seen = set()
    for param in Parameter.objects.filter(star=star, average=False, valid=True):
        key = (param.name.lower(), param.component)
        if key in seen:
            continue
        seen.add(key)
        sync_consensus_cache(star, param.name, param.component)


def refresh_project_consensus(project) -> None:
    """Recompute consensus cache for every star in a project (after policy changes)."""
    from stars.models import Star

    for star in Star.objects.filter(project=project):
        sync_consensus_for_star(star)
