from django.urls import path
from . import views

urlpatterns = [
    # APIs de solo lectura — usadas por el mapa operativo
    path('<int:pk>/espacios/json/', views.muelle_espacios_json, name='muelle_espacios_json'),
    path('zonas/json/',             views.zonas_tierra_json,    name='zonas_tierra_json'),
    path('etiquetas/json/',         views.etiquetas_json,       name='etiquetas_json'),
]