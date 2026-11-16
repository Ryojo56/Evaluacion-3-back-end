from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from cuentas.models import Perfil, Rol

from ...models import Categoria, EstadoPago, Experiencia, Reserva


CLAVE_DEMO = "Demo-Parque-2026!"

CUENTAS = (
    ("admin_demo", "Andrea", Rol.ADMIN),
    ("guia_norte", "Camila", Rol.GUIA),
    ("guia_sur", "Martín", Rol.GUIA),
    ("turista_ana", "Ana", Rol.TURISTA),
    ("turista_luis", "Luis", Rol.TURISTA),
)

CATEGORIAS = {
    "Trekking": "Caminatas interpretativas por senderos de la reserva.",
    "Canopy": "Circuitos de tirolesa con equipo y supervisión.",
    "Kayak": "Remadas guiadas en aguas tranquilas.",
    "Arriendo": "Préstamo de equipo para actividades al aire libre.",
}

EXPERIENCIAS = (
    ("Sendero del Coigüe", "Trekking", "Caminata por bosque nativo de dificultad baja.", 8000, 10),
    ("Canopy entre copas", "Canopy", "Tres tramos de tirolesa con inducción.", 15000, 8),
    ("Kayak en la laguna", "Kayak", "Iniciación con chaleco, remo y guía.", 18000, 6),
    ("Arriendo de bastones", "Arriendo", "Bastones ajustables con retiro en recepción.", 3500, 12),
    ("Mirador del Valle", "Trekking", "Ascenso guiado con parada en el mirador.", 10000, 10),
    ("Circuito del Canelo", "Canopy", "Circuito de cuatro estaciones sobre el bosque.", 17000, 8),
    ("Kayak al atardecer", "Kayak", "Recorrido tranquilo por la orilla sur.", 20000, 6),
    ("Arriendo de casco", "Arriendo", "Retiro y ajuste del casco en recepción.", 4500, 12),
)


class Command(BaseCommand):
    help = "Carga la demostración en una base de datos recién migrada y vacía."

    @transaction.atomic
    def handle(self, *args, **options):
        if any(model.objects.exists() for model in (User, Categoria, Experiencia, Reserva)):
            raise CommandError("Usa una base recién migrada y sin registros del ecoparque.")
        usuarios = {}
        for nombre, nombre_real, rol in CUENTAS:
            usuario = User.objects.create_user(username=nombre, password=CLAVE_DEMO, first_name=nombre_real)
            Perfil.objects.create(usuario=usuario, rol=rol)
            usuarios[nombre] = usuario

        categorias = {
            nombre: Categoria.objects.create(nombre=nombre, descripcion=descripcion)
            for nombre, descripcion in CATEGORIAS.items()
        }
        inicio = timezone.localtime().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=90)
        experiencias = []
        for indice, (titulo, categoria, descripcion, precio, cupo) in enumerate(EXPERIENCIAS):
            guia = "guia_norte" if indice < 4 else "guia_sur"
            experiencias.append(Experiencia.objects.create(
                titulo=titulo, categoria=categorias[categoria], descripcion=descripcion,
                precio=precio, cupo_maximo=cupo, fecha_hora=inicio + timedelta(days=indice),
                creador=usuarios[guia],
            ))

        for turista, indices in (("turista_ana", (0, 1, 4)), ("turista_luis", (2, 5, 6))):
            for posicion, indice in enumerate(indices):
                Reserva.objects.create(
                    usuario=usuarios[turista], experiencia=experiencias[indice],
                    estado_pago=EstadoPago.CONFIRMADO if posicion == 0 else EstadoPago.PENDIENTE,
                )
        self.stdout.write(self.style.SUCCESS("5 usuarios, 4 categorías, 8 experiencias y 6 reservas."))
