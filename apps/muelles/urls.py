# =============================================================================
# urls.py — App: muelles
# Define las rutas de la app muelles. Incluido en config/urls.py bajo el
# prefijo /muelles/.
#
# Todas las rutas son APIs de solo lectura (GET) que alimentan el canvas del
# mapa interactivo en mapa_component.html mediante fetch JS.
#
# Rutas resultantes:
#   GET /muelles/<pk>/espacios/json/ → views.muelle_espacios_json  (name='muelle_espacios_json')
#   GET /muelles/zonas/json/         → views.zonas_tierra_json     (name='zonas_tierra_json')
#   GET /muelles/etiquetas/json/     → views.etiquetas_json        (name='etiquetas_json')
#
# Consumidor principal:
#   - templates/mapa/mapa_component.html  (fetch en JS para construir el canvas)
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # APIs de solo lectura — usadas por el mapa operativo
    path('<int:pk>/espacios/json/', views.muelle_espacios_json, name='muelle_espacios_json'),
    path('zonas/json/',             views.zonas_tierra_json,    name='zonas_tierra_json'),
    path('etiquetas/json/',         views.etiquetas_json,       name='etiquetas_json'),
]