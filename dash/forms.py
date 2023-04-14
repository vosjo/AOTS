from django import forms


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
                                     ] + [(None, "None")])

    color = forms.ChoiceField(label="Color ",
                              required=False,
                              widget=forms.Select(),
                              choices=[
                                          (a, b) for a, b in labeldict.items()
                                      ] + [(None, "None")])

    def get_parameters(self):
        return {'xaxis': self.cleaned_data['xaxis'],
                'yaxis': self.cleaned_data['yaxis'],
                'size': self.cleaned_data['size'],
                'color': self.cleaned_data['color'],
                'nsys': self.cleaned_data["nsys"]}
