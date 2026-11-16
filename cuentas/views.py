from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView

from .forms import AltaUsuarioForm, EditarUsuarioForm
from .models import Perfil, Rol
from .permisos import requiere_rol


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    @transaction.atomic
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        Perfil.objects.create(usuario=self.object, rol=Rol.TURISTA)
        messages.success(self.request, "Cuenta creada. Ya puedes iniciar sesión.")
        return respuesta


@requiere_rol(Rol.ADMIN)
def lista_usuarios(request):
    usuarios = User.objects.prefetch_related("perfiles").order_by("username")
    return render(request, "cuentas/lista.html", {"usuarios": usuarios})


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def guardar_usuario(request, pk=None):
    usuario = get_object_or_404(User, pk=pk) if pk is not None else None
    datos = request.POST if request.method == "POST" else None
    if usuario is None:
        form = AltaUsuarioForm(datos)
    else:
        rol = usuario.perfiles.values_list("rol", flat=True).first()
        form = EditarUsuarioForm(datos, instance=usuario, initial={"rol": Rol.ADMIN if usuario.is_superuser else rol or Rol.TURISTA})
        if usuario == request.user or usuario.is_superuser:
            form.fields["rol"].disabled = True
            form.fields["is_active"].disabled = True
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            guardado = form.save()
            Perfil.objects.update_or_create(usuario=guardado, defaults={"rol": form.cleaned_data["rol"]})
        messages.success(request, "Usuario guardado.")
        return redirect("usuarios")
    return render(request, "panel/formulario.html", {
        "form": form, "titulo": "Editar usuario" if usuario else "Nuevo usuario", "volver": "usuarios",
    })


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario == request.user or usuario.is_superuser:
        messages.error(request, "Esta cuenta de administración está protegida.")
        return redirect("usuarios")
    if request.method == "POST":
        try:
            usuario.delete()
        except ProtectedError:
            messages.error(request, "El usuario tiene experiencias o reservas asociadas. Puedes desactivar su cuenta.")
        else:
            messages.success(request, "Usuario eliminado.")
        return redirect("usuarios")
    return render(request, "panel/eliminar.html", {
        "objeto": usuario, "titulo": "Eliminar usuario", "volver": "usuarios",
    })
