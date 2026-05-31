# =============================================================================
# apps.py — App: asignaciones
# Configuración de la aplicación Django. Django la lee al arrancar para
# registrar la app dentro del proyecto (INSTALLED_APPS en settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# AsignacionesConfig
# Clase de configuración de la app 'asignaciones'. Define el campo auto-
# incrementable por defecto (BigAutoField = entero de 64 bits) y el nombre
# completo de la app tal como aparece en INSTALLED_APPS.
# -----------------------------------------------------------------------------
class AsignacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Tipo de PK por defecto para todos los modelos de esta app
    name = 'apps.asignaciones'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS