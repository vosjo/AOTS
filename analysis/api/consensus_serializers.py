from rest_framework import serializers

from analysis.models.consensus_policy import ConsensusRuleKind, ParameterConsensusPolicy
from analysis.services.parameter_names import normalize_policy_parameter


class ConsensusPolicySerializer(serializers.ModelSerializer):
    preferred_source_name = serializers.CharField(
        source='preferred_source.name',
        read_only=True,
    )
    fallback_preferred_source_name = serializers.CharField(
        source='fallback_preferred_source.name',
        read_only=True,
    )

    class Meta:
        model = ParameterConsensusPolicy
        fields = [
            'id',
            'name',
            'component',
            'rule',
            'preferred_source',
            'preferred_source_name',
            'preferred_analysis_category',
            'source_priority',
            'fallback_rule',
            'fallback_preferred_source',
            'fallback_preferred_source_name',
            'fallback_analysis_category',
            'priority',
        ]
        read_only_fields = ('id', 'preferred_source_name', 'fallback_preferred_source_name')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('name') and data['name'] != '*':
            name, component = normalize_policy_parameter(data['name'], data['component'])
            data['name'] = name
            data['component'] = component
        return data

    def validate(self, attrs):
        if attrs.get('name') and attrs['name'] != '*':
            name = attrs.get('name', getattr(self.instance, 'name', None))
            component = attrs.get(
                'component',
                getattr(self.instance, 'component', 0),
            )
            canonical_name, canonical_component = normalize_policy_parameter(name, component)
            attrs['name'] = canonical_name
            attrs['component'] = canonical_component
        project = self.context.get('project') or getattr(self.instance, 'project', None)
        preferred_source = attrs.get(
            'preferred_source',
            getattr(self.instance, 'preferred_source', None),
        )
        fallback_source = attrs.get(
            'fallback_preferred_source',
            getattr(self.instance, 'fallback_preferred_source', None),
        )
        for source in (preferred_source, fallback_source):
            if source and project and source.project_id != project.id:
                raise serializers.ValidationError('Parameter sources must belong to this project.')
        return attrs


class ConsensusPolicyMetaSerializer(serializers.Serializer):
    @staticmethod
    def rule_choices():
        return ConsensusRuleKind.choices
