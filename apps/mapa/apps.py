# =============================================================================
# apps.py — App: mapa
# Configuración de la aplicación Django para el módulo del mapa interactivo
# y el dashboard de inicio.
# Django la lee al arrancar para registrar la app en el proyecto
# (entrada 'apps.mapa' en INSTALLED_APPS de config/settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# MapaConfig
# Clase de configuración de la app 'mapa'.
# Esta app no define modelos propios; toda su lógica está en views.py y
# en el submódulo services/marine_api.py.
# -----------------------------------------------------------------------------
class MapaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Sin uso real (no hay modelos)
    name = 'apps.mapa'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS