from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Rol


class AltaUsuarioForm(UserCreationForm):
    rol = forms.ChoiceField(choices=Rol.choices, initial=Rol.TURISTA)

    class Meta(UserCreationForm.Meta):
        fields = ["username", "first_name", "last_name", "email"]


class EditarUsuarioForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=Rol.choices)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
