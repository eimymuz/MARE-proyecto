# =============================================================================
# urls.py — App: mapa
# Define las rutas de la app mapa. Incluido en config/urls.py bajo el prefijo /mapa/.
# La vista 'inicio' NO se registra aquí; se registra directamente en config/urls.py
# bajo la ruta raíz '/'.
#
# Rutas resultantes:
#   GET  /mapa/               → views.mapa_view          (name='mapa')
#   GET  /mapa/disponibilidad/ → views.disponibilidad_json (name='mapa_disponibilidad')
#   POST /mapa/asignar/       → views.asignar_espacio    (name='mapa_asignar')
#
# Consumidores de estas URLs:
#   - templates/mapa/mapa.html          (enlace al mapa y llamadas AJAX)
#   - templates/mapa/mapa_component.html (fetch a mapa_disponibilidad y mapa_asignar)
#   - templates/solicitudes/solicitud_list.html     (botón "Asignar" → ?solicitud_id=N)
#   - templates/solicitudes/solicitud_aprobadas.html (botón "Reasignar")
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    path('',                views.mapa_view,           name='mapa'),
    path('disponibilidad/', views.disponibilidad_json, name='mapa_disponibilidad'),
    path('asignar/',        views.asignar_espacio,     name='mapa_asignar'),
]