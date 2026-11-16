from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("cuentas/", include("cuentas.urls")),
    path("experiencias/", include("experiencias.urls")),
]
