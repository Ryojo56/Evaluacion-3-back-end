from django.urls import path

from . import views

urlpatterns = [
    path("catalogo/", views.catalogo, name="catalogo"),
    path("categorias/", views.categorias, name="categorias"),
    path("categorias/nueva/", views.guardar_categoria, name="categoria_nueva"),
    path("categorias/<int:pk>/editar/", views.guardar_categoria, name="categoria_editar"),
    path("categorias/<int:pk>/eliminar/", views.eliminar_categoria, name="categoria_eliminar"),
    path("", views.experiencias, name="experiencias"),
    path("nueva/", views.guardar_experiencia, name="experiencia_nueva"),
    path("<int:pk>/editar/", views.guardar_experiencia, name="experiencia_editar"),
    path("<int:pk>/eliminar/", views.eliminar_experiencia, name="experiencia_eliminar"),
    path("<int:pk>/reservar/", views.reservar, name="reservar"),
    path("reservas/", views.reservas, name="reservas"),
    path("reservas/nueva/", views.alta_reserva, name="reserva_nueva"),
    path("reservas/<int:pk>/editar/", views.editar_reserva, name="reserva_editar"),
    path("reservas/<int:pk>/eliminar/", views.eliminar_reserva, name="reserva_eliminar"),
    path("reservas/<int:pk>/pagar/", views.pagar_reserva, name="reserva_pagar"),
]
