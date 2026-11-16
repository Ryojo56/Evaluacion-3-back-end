from django.conf import settings
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ExperienciaQuerySet(models.QuerySet):
    def disponibles(self):
        return self.filter(activa=True, categoria__activa=True, fecha_hora__gt=timezone.now())


class Experiencia(models.Model):
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    cupo_maximo = models.PositiveIntegerField()
    fecha_hora = models.DateTimeField()
    activa = models.BooleanField(default=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="experiencias")
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="experiencias_creadas")

    objects = ExperienciaQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(precio__gte=0), name="experiencia_precio_no_negativo"),
            models.CheckConstraint(condition=models.Q(cupo_maximo__gt=0), name="experiencia_cupo_positivo"),
        ]

    def __str__(self):
        return self.titulo


class EstadoPago(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    CONFIRMADO = "confirmado", "Confirmado"


class Reserva(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas")
    experiencia = models.ForeignKey(Experiencia, on_delete=models.PROTECT, related_name="reservas")
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado_pago = models.CharField(max_length=10, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario", "experiencia"], name="reserva_unica_por_experiencia"),
            models.CheckConstraint(condition=models.Q(estado_pago__in=EstadoPago.values), name="reserva_estado_valido"),
        ]

    def __str__(self):
        return f"{self.experiencia} · {self.usuario}"
