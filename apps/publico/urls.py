# =============================================================================
# urls.py — App: publico
# Define las rutas públicas del sistema (sin autenticación requerida).
# Incluido en config/urls.py bajo el prefijo /publico/ o directamente en /.
#
# Rutas resultantes:
#   GET  /           → views.landing          (name='landing')
#   POST /solicitar/ → views.solicitud_submit (name='solicitud_submit')
#
# Consumidores:
#   - templates/publico/landing.html  (formulario de solicitud → fetch POST a 'solicitud_submit')
#   - templates/components/navbar.html (enlace al landing para visitantes no autenticados)
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    path('',           views.landing,          name='landing'),
    path('solicitar/', views.solicitud_submit,  name='solicitud_submit'),
]