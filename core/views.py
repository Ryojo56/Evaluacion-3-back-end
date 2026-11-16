from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from cuentas.models import Rol
from cuentas.permisos import rol_usuario
from experiencias.models import Categoria, Experiencia, Reserva


def inicio(request):
    return render(request, "home.html", {
        "destacadas": Experiencia.objects.disponibles().select_related("categoria").order_by("fecha_hora")[:3],
    })


@login_required
def panel(request):
    rol = rol_usuario(request.user)
    if rol == Rol.ADMIN:
        cifras = [
            ("Experiencias", Experiencia.objects.count(), "experiencias"),
            ("Categorías", Categoria.objects.count(), "categorias"),
            ("Reservas", Reserva.objects.count(), "reservas"),
        ]
    elif rol == Rol.GUIA:
        cifras = [("Mis experiencias", Experiencia.objects.filter(creador=request.user).count(), "experiencias")]
    elif rol == Rol.TURISTA:
        cifras = [
            ("Mis reservas", Reserva.objects.filter(usuario=request.user).count(), "reservas"),
            ("Experiencias disponibles", Experiencia.objects.disponibles().count(), "catalogo"),
        ]
    else:
        raise PermissionDenied
    return render(request, "panel/inicio.html", {"cifras": cifras})
