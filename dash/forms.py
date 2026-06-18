from django import forms

from analysis.parameter_labels import hrd_axis_choices, normalize_hrd_axis_key


def _normalize_hrd_form_data(data):
    if not data:
        return data
    mutable = data.copy()
    for key in ('xaxis', 'yaxis', 'size', 'color'):
        if mutable.get(key):
            mutable[key] = normalize_hrd_axis_key(mutable[key])
    return mutable


class HRDPlotterForm(forms.Form):
    nsys = forms.ChoiceField(label="# Systems ",
                             required=True,
                             widget=forms.Select(),
                             choices=(
                                 (50, "50"),
                                 (100, "100"),
                                 (500, "500"),
                                 (1000, "1000"),
                                 (2500, "2500"),
                                 # ("all", "All")
                             ))

    xaxis = forms.ChoiceField(label="X-axis ",
                              required=True,
                              widget=forms.Select(),
                              choices=hrd_axis_choices())

    yaxis = forms.ChoiceField(label="Y-axis ",
                              required=True,
                              widget=forms.Select(),
                              choices=hrd_axis_choices())

    size = forms.ChoiceField(label="Size ",
                             required=False,
                             widget=forms.Select(),
                             choices=hrd_axis_choices() + [(None, "None")])

    color = forms.ChoiceField(label="Color ",
                              required=False,
                              widget=forms.Select(),
                              choices=hrd_axis_choices() + [(None, "None")])

    def __init__(self, *args, **kwargs):
        if args and hasattr(args[0], 'copy'):
            args = (_normalize_hrd_form_data(args[0]),) + args[1:]
        super().__init__(*args, **kwargs)

    def get_parameters(self):
        return {'xaxis': self.cleaned_data['xaxis'],
                'yaxis': self.cleaned_data['yaxis'],
                'size': self.cleaned_data['size'],
                'color': self.cleaned_data['color'],
                'nsys': self.cleaned_data["nsys"]}
