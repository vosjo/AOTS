from django import forms

from analysis.categories import upload_category_choices
from analysis.models import Parameter
from analysis.parameter_labels import parameter_label_with_unit


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
        parameter_rows = (
            param_qs.filter(average=True)
            .values('cname', 'unit')
            .distinct()
            .order_by('cname')
        )
        parameter_names = [
            (
                row['cname'],
                parameter_label_with_unit(row['cname'], row['unit'], from_cname=True),
            )
            for row in parameter_rows
        ]

        self.fields['xaxis'].choices = parameter_names
        self.fields['yaxis'].choices = parameter_names
        parameter_names_with_empty = parameter_names + [('', '(none)')]
        self.fields['size'].choices = parameter_names_with_empty
        self.fields['color'].choices = parameter_names_with_empty

        choice_values = [name for name, _ in parameter_names]

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
