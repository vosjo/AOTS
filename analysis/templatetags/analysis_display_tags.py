from django import template

from analysis.services.analysis_display import get_component_parameters, get_system_parameters

register = template.Library()


@register.simple_tag
def analysis_system_parameters(analysis):
    return get_system_parameters(analysis)


@register.simple_tag
def analysis_component_parameters(analysis):
    return get_component_parameters(analysis)
