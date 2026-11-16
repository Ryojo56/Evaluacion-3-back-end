from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("entrar/", LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("registro/", views.SignUpView.as_view(), name="signup"),
    path("usuarios/", views.lista_usuarios, name="usuarios"),
    path("usuarios/nuevo/", views.guardar_usuario, name="usuario_nuevo"),
    path("usuarios/<int:pk>/editar/", views.guardar_usuario, name="usuario_editar"),
    path("usuarios/<int:pk>/eliminar/", views.eliminar_usuario, name="usuario_eliminar"),
]
