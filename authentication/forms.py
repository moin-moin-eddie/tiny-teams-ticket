from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Benutzername",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Passwort",
                "class": "form-control"
            }
        ))


class CreateUserForm(forms.Form):
    email = forms.EmailField(label="Email-Adresse")
    name = forms.CharField(label="Vor- & Nachname")