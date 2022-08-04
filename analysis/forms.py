from django import forms

from analysis.models import Parameter


class UploadAnalysisFileForm(forms.Form):
    datafile = forms.FileField(label='Select a file',
                               widget=forms.ClearableFileInput(attrs={'multiple': True}))


class ParameterPlotterForm(forms.Form):
    xaxis = forms.ChoiceField(label="x-axis ", required=False,
                              widget=forms.Select())

    yaxis = forms.ChoiceField(label="y-axis ", required=False,
                              widget=forms.Select())

    size = forms.ChoiceField(label="size ", required=False,
                             widget=forms.Select())

    color = forms.ChoiceField(label="color ", required=False,
                              widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parameterNames = sorted(Parameter.objects.values_list('cname', 'cname').distinct())

        self.fields['xaxis'].choices = parameterNames
        self.fields['yaxis'].choices = parameterNames
        parameterNames.append(('', ''))
        self.fields['size'].choices = parameterNames
        self.fields['color'].choices = parameterNames

        inix = 'p' if ('p', 'p') in parameterNames else parameterNames[0][0]
        if len(parameterNames) > 1:
            iniy = 'q' if ('q', 'q') in parameterNames else parameterNames[1][0]
        else:
            iniy = parameterNames[0][1]
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
        return {'xaxis': self.clean_xaxis(),
                'yaxis': self.clean_yaxis(),
                'size': self.cleaned_data['size'],
                'color': self.cleaned_data['color'], }


class HRDPlotterForm(forms.Form):
    from .labels import labeldict
    nsys = forms.ChoiceField(label="# Systems ",
                             required=True,
                             widget=forms.Select(),
                             choices=(
                                 (50, "50"),
                                 (100, "100"),
                                 (500, "500"),
                                 ("all", "All")
                             ))

    xaxis = forms.ChoiceField(label="X-axis ",
                              required=True,
                              widget=forms.Select(),
                              choices=[
                                  (a, b) for a, b in labeldict.items()
                              ])

    yaxis = forms.ChoiceField(label="Y-axis ",
                              required=True,
                              widget=forms.Select(),
                              choices=[
                                  (a, b) for a, b in labeldict.items()
                              ])

    size = forms.ChoiceField(label="Size ",
                             required=False,
                             widget=forms.Select(),
                             choices=[
                                  (a, b) for a, b in labeldict.items()
                              ]+[(None, "None")])

    color = forms.ChoiceField(label="Color ",
                              required=False,
                              widget=forms.Select(),
                              choices=[
                                  (a, b) for a, b in labeldict.items()
                              ]+[(None, "None")])

    def get_parameters(self):
        return {'xaxis': self.cleaned_data['xaxis'],
                'yaxis': self.cleaned_data['yaxis'],
                'size': self.cleaned_data['size'],
                'color': self.cleaned_data['color'],
                'nsys': self.cleaned_data["nsys"]}
