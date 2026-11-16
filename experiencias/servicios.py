from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import EstadoPago, Experiencia, Reserva


@transaction.atomic
def crear_reserva(usuario, experiencia_id, estado_pago=EstadoPago.PENDIENTE):
    experiencia = get_object_or_404(Experiencia.objects.select_for_update(), pk=experiencia_id)
    if not Experiencia.objects.disponibles().filter(pk=experiencia_id).exists():
        raise ValidationError("Esta experiencia ya no está disponible para reservar.")
    if experiencia.reservas.filter(usuario=usuario).exists():
        raise ValidationError("Ya tienes una reserva para esta experiencia.")
    if experiencia.reservas.count() >= experiencia.cupo_maximo:
        raise ValidationError("Esta experiencia ya no tiene cupos.")
    return Reserva.objects.create(usuario=usuario, experiencia=experiencia, estado_pago=estado_pago)
