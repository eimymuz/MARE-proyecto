# =============================================================================
# urls.py — App: embarcaciones
# Sin rutas definidas. Las embarcaciones no tienen vistas propias.
#
# Flujos relacionados con embarcaciones:
#   - Creación → apps/publico/urls.py  (formulario público de solicitud)
#   - Gestión  → /admin/              (panel de administración de Django)
# =============================================================================

from django.urls import path
from . import views  # Sin uso actual

urlpatterns = [
    # Sin rutas definidas por el momento
]