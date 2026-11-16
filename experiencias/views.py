from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from cuentas.models import Rol
from cuentas.permisos import requiere_rol, rol_usuario

from .forms import AltaReservaForm, CategoriaForm, EstadoReservaForm, ExperienciaForm
from .models import Categoria, EstadoPago, Experiencia, Reserva
from .servicios import crear_reserva


def catalogo(request):
    items = Experiencia.objects.disponibles().select_related("categoria").annotate(
        ocupados=Count("reservas")
    ).order_by("fecha_hora")
    return render(request, "experiencias/catalogo.html", {"experiencias": items})


@requiere_rol(Rol.ADMIN)
def categorias(request):
    return render(request, "experiencias/categorias.html", {
        "categorias": Categoria.objects.order_by("nombre"),
    })


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def guardar_categoria(request, pk=None):
    categoria = get_object_or_404(Categoria, pk=pk) if pk is not None else None
    form = CategoriaForm(request.POST if request.method == "POST" else None, instance=categoria)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría guardada.")
        return redirect("categorias")
    return render(request, "panel/formulario.html", {
        "form": form, "titulo": "Editar categoría" if categoria else "Nueva categoría", "volver": "categorias",
    })


def confirmar_borrado(request, objeto, titulo, volver, mensaje_protegido):
    if request.method == "POST":
        try:
            objeto.delete()
        except ProtectedError:
            messages.error(request, mensaje_protegido)
        else:
            messages.success(request, "Registro eliminado.")
        return redirect(volver)
    return render(request, "panel/eliminar.html", {"objeto": objeto, "titulo": titulo, "volver": volver})


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def eliminar_categoria(request, pk):
    return confirmar_borrado(request, get_object_or_404(Categoria, pk=pk), "Eliminar categoría", "categorias",
                             "La categoría tiene experiencias asociadas. Puedes desactivarla.")


def experiencias_del_operador(usuario):
    if rol_usuario(usuario) == Rol.GUIA:
        return Experiencia.objects.filter(creador=usuario)
    return Experiencia.objects.all()


@requiere_rol(Rol.ADMIN, Rol.GUIA)
def experiencias(request):
    items = experiencias_del_operador(request.user).select_related("categoria", "creador").order_by("fecha_hora")
    return render(request, "experiencias/lista.html", {"experiencias": items})


@requiere_rol(Rol.ADMIN, Rol.GUIA)
@require_http_methods(["GET", "POST"])
def guardar_experiencia(request, pk=None):
    queryset = experiencias_del_operador(request.user)
    with transaction.atomic():
        if request.method == "POST":
            queryset = queryset.select_for_update()
        experiencia = get_object_or_404(queryset, pk=pk) if pk is not None else None
        form = ExperienciaForm(request.POST if request.method == "POST" else None, instance=experiencia)
        if request.method == "POST" and form.is_valid():
            guardada = form.save(commit=False)
            if experiencia is None:
                guardada.creador = request.user
            guardada.save()
            messages.success(request, "Experiencia guardada.")
            return redirect("experiencias")
    return render(request, "panel/formulario.html", {
        "form": form, "titulo": "Editar experiencia" if experiencia else "Nueva experiencia", "volver": "experiencias",
    })


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def eliminar_experiencia(request, pk):
    return confirmar_borrado(request, get_object_or_404(Experiencia, pk=pk), "Eliminar experiencia", "experiencias",
                             "La experiencia tiene reservas asociadas. Puedes desactivarla.")


def reservas_visibles(usuario):
    queryset = Reserva.objects.select_related("usuario", "experiencia")
    if rol_usuario(usuario) == Rol.TURISTA:
        return queryset.filter(usuario=usuario)
    return queryset


@requiere_rol(Rol.ADMIN, Rol.TURISTA)
def reservas(request):
    return render(request, "experiencias/reservas.html", {
        "reservas": reservas_visibles(request.user).order_by("-fecha_inscripcion"),
    })


@requiere_rol(Rol.TURISTA)
@require_POST
def reservar(request, pk):
    try:
        crear_reserva(request.user, pk)
    except ValidationError as error:
        messages.error(request, error.message)
        return redirect("catalogo")
    messages.success(request, "Reserva creada con pago pendiente.")
    return redirect("reservas")


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def alta_reserva(request):
    form = AltaReservaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            crear_reserva(form.cleaned_data["usuario"], form.cleaned_data["experiencia"].pk,
                          form.cleaned_data["estado_pago"])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Reserva creada.")
            return redirect("reservas")
    return render(request, "panel/formulario.html", {"form": form, "titulo": "Nueva reserva", "volver": "reservas"})


@requiere_rol(Rol.ADMIN)
@require_http_methods(["GET", "POST"])
def editar_reserva(request, pk):
    with transaction.atomic():
        queryset = Reserva.objects
        if request.method == "POST":
            queryset = queryset.select_for_update()
        reserva = get_object_or_404(queryset, pk=pk)
        form = EstadoReservaForm(request.POST if request.method == "POST" else None, instance=reserva)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "Estado de pago actualizado.")
            return redirect("reservas")
    return render(request, "panel/formulario.html", {
        "form": form, "titulo": "Editar estado de pago", "objeto": reserva, "volver": "reservas",
    })


@requiere_rol(Rol.ADMIN, Rol.TURISTA)
@require_http_methods(["GET", "POST"])
def eliminar_reserva(request, pk):
    with transaction.atomic():
        queryset = reservas_visibles(request.user)
        if request.method == "POST":
            queryset = queryset.select_related(None).select_for_update()
        reserva = get_object_or_404(queryset, pk=pk)
        if rol_usuario(request.user) == Rol.TURISTA and reserva.estado_pago != EstadoPago.PENDIENTE:
            raise PermissionDenied
        titulo = "Cancelar reserva" if rol_usuario(request.user) == Rol.TURISTA else "Eliminar reserva"
        return confirmar_borrado(request, reserva, titulo, "reservas", "La reserva tiene registros asociados.")


@requiere_rol(Rol.TURISTA)
@require_http_methods(["GET", "POST"])
def pagar_reserva(request, pk):
    # Pago simulado: el turista confirma el pago de una reserva propia pendiente.
    with transaction.atomic():
        queryset = Reserva.objects.filter(usuario=request.user)
        if request.method == "POST":
            queryset = queryset.select_for_update()
        reserva = get_object_or_404(queryset.select_related("experiencia"), pk=pk)
        if reserva.estado_pago != EstadoPago.PENDIENTE:
            messages.info(request, "Esta reserva ya está pagada.")
            return redirect("reservas")
        if request.method == "POST":
            reserva.estado_pago = EstadoPago.CONFIRMADO
            reserva.save(update_fields=["estado_pago"])
            messages.success(request, f"Pago de ${reserva.experiencia.precio} confirmado para {reserva.experiencia}.")
            return redirect("reservas")
    return render(request, "experiencias/pagar.html", {"reserva": reserva})
