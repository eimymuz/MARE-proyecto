# =============================================================================
# apps.py — App: embarcaciones
# Configuración de la aplicación Django para el módulo de embarcaciones.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.embarcaciones' en INSTALLED_APPS de config/settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# EmbarcacionesConfig
# Clase de configuración de la app 'embarcaciones'.
# Define el tipo de PK por defecto y el nombre de la app.
# -----------------------------------------------------------------------------
class EmbarcacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # PK BigInt (64 bits) para todos los modelos de esta app
    name = 'apps.embarcaciones'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS