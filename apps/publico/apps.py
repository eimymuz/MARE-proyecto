# =============================================================================
# apps.py — App: publico
# Configuración de la aplicación Django para el módulo público.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.publico' en INSTALLED_APPS de config/settings.py).
#
# Esta app es la única del proyecto que expone rutas sin @login_required,
# permitiendo a clientes externos enviar solicitudes de ingreso a la marina.
# No define modelos propios: escribe en modelos de clientes, embarcaciones
# y solicitudes.
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# PublicoConfig
# Clase de configuración de la app 'publico'.
# -----------------------------------------------------------------------------
class PublicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Sin uso real (no hay modelos propios)
    name = 'apps.publico'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS
