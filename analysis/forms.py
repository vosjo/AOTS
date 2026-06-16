from django import forms

from analysis.categories import upload_category_choices
from analysis.models import Parameter


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class UploadAnalysisFileForm(forms.Form):
    datafile = MultipleFileField(label='Select a file')
    category = forms.ChoiceField(
        label='Category',
        required=False,
        choices=upload_category_choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = upload_category_choices()


class ParameterPlotterForm(forms.Form):
    xaxis = forms.ChoiceField(label="X-axis ", required=False,
                              widget=forms.Select())

    yaxis = forms.ChoiceField(label="Y-axis ", required=False,
                              widget=forms.Select())

    size = forms.ChoiceField(label="Size ", required=False,
                             widget=forms.Select())

    color = forms.ChoiceField(label="Color ", required=False,
                              widget=forms.Select())

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

        param_qs = Parameter.objects.all()
        if project is not None:
            param_qs = param_qs.filter(star__project=project)
        parameterNames = sorted(param_qs.values_list('cname', 'cname').distinct())

        self.fields['xaxis'].choices = parameterNames
        self.fields['yaxis'].choices = parameterNames
        parameterNames.append(('', ''))
        self.fields['size'].choices = parameterNames
        self.fields['color'].choices = parameterNames

        choice_values = [name for name, _ in parameterNames]

        def pick(names, preferred, fallback_index=0):
            if preferred in names:
                return preferred
            if not names:
                return ''
            idx = min(fallback_index, len(names) - 1)
            return names[idx]

        inix = pick(choice_values, 'parallax')
        iniy = pick(choice_values, 'pmdec', 1)
        self.initial['xaxis'] = inix
        self.initial['yaxis'] = iniy
        self.initial['size'] = ''
        self.initial['color'] = ''

    def clean_xaxis(self):
        if not self['xaxis'].html_name in self.data:
            return self.initial['xaxis']
        else:
            return self.cleaned_data['xaxis']

    def clean_yaxis(self):
        if not self['yaxis'].html_name in self.data:
            return self.initial['yaxis']
        else:
            return self.cleaned_data['yaxis']

    def get_parameters(self):
        if self.is_bound and self.is_valid():
            return {
                'xaxis': self.cleaned_data['xaxis'],
                'yaxis': self.cleaned_data['yaxis'],
                'size': self.cleaned_data.get('size', ''),
                'color': self.cleaned_data.get('color', ''),
            }
        return {
            'xaxis': self.initial['xaxis'],
            'yaxis': self.initial['yaxis'],
            'size': self.initial.get('size', ''),
            'color': self.initial.get('color', ''),
        }
