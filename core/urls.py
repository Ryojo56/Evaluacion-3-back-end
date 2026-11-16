from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="home"),
    path("panel/", views.panel, name="panel"),
]
