from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Rol


def rol_usuario(usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        return None
    # Se guarda en el objeto para no repetir la consulta en la misma petición.
    if not hasattr(usuario, "_rol_cache"):
        if usuario.is_superuser:
            usuario._rol_cache = Rol.ADMIN
        else:
            usuario._rol_cache = usuario.perfiles.values_list("rol", flat=True).first()
    return usuario._rol_cache


def requiere_rol(*roles):
    def decorador(vista):
        @login_required
        @wraps(vista)
        def protegida(request, *args, **kwargs):
            if rol_usuario(request.user) not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return protegida

    return decorador


def rol_en_plantilla(request):
    return {"rol_actual": rol_usuario(request.user)}
