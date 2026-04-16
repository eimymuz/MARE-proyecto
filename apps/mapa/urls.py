from django.urls import path
from . import views

urlpatterns = [
    path('',               views.mapa_view,           name='mapa'),
    path('disponibilidad/', views.disponibilidad_json, name='mapa_disponibilidad'),
    path('asignar/',        views.asignar_espacio,     name='mapa_asignar'),
]