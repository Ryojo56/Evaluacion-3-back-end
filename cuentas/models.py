from django.conf import settings
from django.db import models


class Rol(models.TextChoices):
    ADMIN = "admin", "Administrador"
    GUIA = "guia", "Guía / Operador"
    TURISTA = "turista", "Turista / Cliente"


class Perfil(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfiles")
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.TURISTA)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario"], name="perfil_unico_por_usuario"),
        ]

    def __str__(self):
        return f"{self.usuario} · {self.get_rol_display()}"
