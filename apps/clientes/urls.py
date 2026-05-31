# =============================================================================
# urls.py — App: clientes
# Sin rutas definidas. Los clientes no tienen vistas propias en esta app.
#
# Flujos relacionados con clientes:
#   - Creación → apps/publico/urls.py  (formulario público de solicitud)
#   - Gestión  → /admin/  (panel de administración de Django)
# =============================================================================

from django.urls import path
from . import views  # Importado por defecto; sin uso actual

urlpatterns = [
    # Sin rutas definidas por el momento
]