# =============================================================================
# urls.py — App: asignaciones
# Define las rutas URL propias de la app asignaciones.
# Este archivo es incluido desde el urls.py principal del proyecto.
# Actualmente no tiene rutas registradas: las operaciones de asignación
# se manejan desde la app 'solicitudes' (apps/solicitudes/urls.py).
# =============================================================================

from django.urls import path
from . import views  # Importa las vistas de esta app (actualmente vacías)

urlpatterns = [
    # Sin rutas definidas por el momento
]