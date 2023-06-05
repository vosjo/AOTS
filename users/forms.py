from django import forms


class ChangeProPicForm(forms.Form):
    newpic = forms.FileField(label='Select a new profile picture',
                             widget=forms.ClearableFileInput(attrs={'multiple': False}))