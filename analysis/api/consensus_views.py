"""REST API for project parameter consensus policies."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from analysis.api.consensus_serializers import (
    ConsensusPolicyMetaSerializer,
    ConsensusPolicySerializer,
)
from analysis.categories import AnalysisCategory
from analysis.models import Analysis, Parameter, ParameterConsensusPolicy, ParameterSource
from analysis.models.default_values import COMPONENT_CHOICES, DEFAULT_PARAMETERS, canonical_parameter_base
from analysis.models.parameter_source import ParameterSourceKind
from analysis.parameter_labels import (
    group_consensus_parameter_choices,
    normalize_parameter_name,
    parameter_label_with_unit,
    serialize_plotter_choices,
)
from analysis.services.parameter_names import normalize_policy_parameter
from analysis.services.parameter_consensus import refresh_project_consensus
from stars.models import Project


def _project_for_request(request, slug: str) -> Project:
    project = get_object_or_404(Project, slug=slug)
    if request.user.is_anonymous and not project.is_public:
        raise PermissionDenied()
    if not request.user.is_anonymous and not request.user.can_read(project):
        raise PermissionDenied()
    return project


def _require_project_editor(request, project: Project) -> None:
    if request.user.is_anonymous or not request.user.can_add(project):
        raise PermissionDenied()


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def consensus_policies_list_create(request, project_slug):
    project = _project_for_request(request, project_slug)

    if request.method == 'GET':
        policies = ParameterConsensusPolicy.objects.filter(project=project).order_by('name', 'component')
        return Response(ConsensusPolicySerializer(policies, many=True).data)

    _require_project_editor(request, project)
    serializer = ConsensusPolicySerializer(
        data=request.data,
        context={'project': project},
    )
    serializer.is_valid(raise_exception=True)
    policy = serializer.save(project=project)
    refresh_project_consensus(project)
    return Response(ConsensusPolicySerializer(policy).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def consensus_policy_detail(request, project_slug, pk):
    project = _project_for_request(request, project_slug)
    policy = get_object_or_404(ParameterConsensusPolicy, pk=pk, project=project)

    if request.method == 'GET':
        return Response(ConsensusPolicySerializer(policy).data)

    _require_project_editor(request, project)

    if request.method == 'DELETE':
        policy.delete()
        refresh_project_consensus(project)
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ConsensusPolicySerializer(
        policy,
        data=request.data,
        partial=True,
        context={'project': project},
    )
    serializer.is_valid(raise_exception=True)
    policy = serializer.save()
    refresh_project_consensus(project)
    return Response(ConsensusPolicySerializer(policy).data)


def _parameter_default_unit(name: str) -> str | None:
    base = normalize_parameter_name(name)
    if base in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[base]
    if name in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[name]
    canonical = canonical_parameter_base(base)
    if canonical in DEFAULT_PARAMETERS:
        return DEFAULT_PARAMETERS[canonical]
    for key, unit in DEFAULT_PARAMETERS.items():
        if canonical_parameter_base(key) == canonical:
            return unit
    return None


def _consensus_policy_parameter_bases(project) -> set[str]:
    bases = {'*'}
    for key in DEFAULT_PARAMETERS:
        bases.add(normalize_parameter_name(key))
    for name in (
        Parameter.objects.filter(star__project=project, valid=True, average=False)
        .values_list('name', flat=True)
        .distinct()
    ):
        bases.add(normalize_parameter_name(name))
    return bases


def _parameter_choice_label(name: str) -> str:
    if name == '*':
        return 'All parameters (*)'
    base = normalize_parameter_name(name)
    return parameter_label_with_unit(base, _parameter_default_unit(base))


@api_view(['GET'])
@permission_classes([AllowAny])
def consensus_policies_meta(request, project_slug):
    project = _project_for_request(request, project_slug)

    parameter_names = sorted(_consensus_policy_parameter_bases(project))
    flat_parameter_choices = sorted(
        (
            (name, _parameter_choice_label(name))
            for name in parameter_names
        ),
        key=lambda item: (item[0] != '*', item[1].lower()),
    )
    parameter_choices = serialize_plotter_choices(
        group_consensus_parameter_choices(flat_parameter_choices),
    )

    analysis_ids = Analysis.objects.filter(project=project).values_list('pk', flat=True)
    sources = list(
        ParameterSource.objects.filter(project=project, kind=ParameterSourceKind.CATALOG)
        .exclude(pk__in=analysis_ids)
        .order_by('name')
        .values('id', 'name', 'kind')
    )

    categories = [
        {'value': value, 'label': label}
        for value, label in AnalysisCategory.choices
    ]

    components = [
        {'value': value, 'label': label}
        for value, label in COMPONENT_CHOICES
    ]

    return Response({
        'parameter_names': parameter_names,
        'parameter_choices': parameter_choices,
        'wildcard': '*',
        'sources': sources,
        'analysis_categories': categories,
        'components': components,
        'rules': [
            {'value': value, 'label': label}
            for value, label in ConsensusPolicyMetaSerializer.rule_choices()
        ],
    })
