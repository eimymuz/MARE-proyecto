# =============================================================================
# urls.py — App: solicitudes
# Define las rutas del módulo de solicitudes. Incluido en config/urls.py
# bajo el prefijo /solicitudes/.
#
# Rutas resultantes:
#   GET      /solicitudes/                          → solicitud_list            (name='solicitud_list')
#   GET      /solicitudes/en-espera/               → solicitud_en_espera_list  (name='solicitud_en_espera_list')
#   GET      /solicitudes/aprobadas/               → solicitud_aprobadas_list  (name='solicitud_aprobadas_list')
#   GET/POST /solicitudes/<pk>/editar/             → solicitud_update           (name='solicitud_update')
#   POST     /solicitudes/<pk>/estado/<nuevo_estado>/ → solicitud_cambiar_estado (name='solicitud_cambiar_estado')
#   GET      /solicitudes/<pk>/json/               → solicitud_detalle_json     (name='solicitud_detalle_json')
#
# Consumidores principales:
#   - templates/solicitudes/solicitud_list.html      (lista PENDIENTE y EN_ESPERA)
#   - templates/solicitudes/solicitud_aprobadas.html (lista APROBADA)
#   - templates/solicitudes/solicitud_form.html      (formulario de edición)
#   - templates/components/modal_rechazo.html        (POST a solicitud_cambiar_estado)
#   - templates/components/popup_solicitud.html      (fetch GET a solicitud_detalle_json)
#   - templates/components/navbar.html               (enlaces de navegación por estado)
#   - templates/mapa/mapa.html                       (enlace al mapa con ?solicitud_id=)
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # Listados por estado
    path('',                                        views.solicitud_list,           name='solicitud_list'),
    path('en-espera/',                              views.solicitud_en_espera_list, name='solicitud_en_espera_list'),
    path('aprobadas/',                              views.solicitud_aprobadas_list, name='solicitud_aprobadas_list'),

    # Edición y cambio de estado
    path('<int:pk>/editar/',                        views.solicitud_update,         name='solicitud_update'),
    path('<int:pk>/estado/<str:nuevo_estado>/',     views.solicitud_cambiar_estado, name='solicitud_cambiar_estado'),

    # API JSON para el popup de detalle
    path('<int:pk>/json/',                          views.solicitud_detalle_json,   name='solicitud_detalle_json'),
]