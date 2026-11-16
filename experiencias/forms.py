from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

from cuentas.models import Rol

from .models import Categoria, EstadoPago, Experiencia, Reserva


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activa"]


class ExperienciaForm(forms.ModelForm):
    class Meta:
        model = Experiencia
        fields = ["titulo", "descripcion", "precio", "cupo_maximo", "fecha_hora", "categoria", "activa"]
        labels = {"precio": "Precio en pesos chilenos"}
        widgets = {
            "fecha_hora": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cupo_maximo"].validators.append(MinValueValidator(1))
        self.fields["precio"].validators.append(MinValueValidator(0))

    def clean_cupo_maximo(self):
        cupo = self.cleaned_data["cupo_maximo"]
        if self.instance.pk and cupo < self.instance.reservas.count():
            raise forms.ValidationError("El cupo es menor que la cantidad de reservas existentes.")
        return cupo


class AltaReservaForm(forms.Form):
    usuario = forms.ModelChoiceField(
        label="Turista",
        queryset=User.objects.filter(is_active=True, is_superuser=False, perfiles__rol=Rol.TURISTA).order_by("username"),
    )
    experiencia = forms.ModelChoiceField(queryset=Experiencia.objects.none())
    estado_pago = forms.ChoiceField(choices=EstadoPago.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["experiencia"].queryset = Experiencia.objects.disponibles().order_by("fecha_hora")


class EstadoReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ["estado_pago"]
