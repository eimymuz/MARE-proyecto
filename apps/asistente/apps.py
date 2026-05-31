# =============================================================================
# apps.py — App: asistente
# Configuración de la aplicación Django para el módulo del chatbot Coral.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.asistente' en INSTALLED_APPS de config/settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# AsistenteConfig
# Clase de configuración de la app 'asistente'.
# Esta app no define modelos propios; su única responsabilidad es exponer
# el endpoint del chatbot (views.py + urls.py).
# -----------------------------------------------------------------------------
class AsistenteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Tipo de PK por defecto (no se usa, no hay modelos)
    name = 'apps.asistente'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS
