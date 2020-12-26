from django import forms

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class InputForm(forms.Form):
    input = forms.CharField(required=False,label=False)