# =============================================================================
# apps.py — App: usuarios
# Configuración de la aplicación Django para el módulo de autenticación y
# gestión de usuarios del sistema MARE.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.usuarios' en INSTALLED_APPS de config/settings.py).
#
# Esta app no define modelos propios: usa User de Django Auth y Administrador
# de apps.asignaciones para manejar la identidad y los roles del sistema.
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# UsuariosConfig
# Clase de configuración de la app 'usuarios'.
# -----------------------------------------------------------------------------
class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Sin uso real (no hay modelos propios)
    name = 'apps.usuarios'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS