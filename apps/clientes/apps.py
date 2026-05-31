# =============================================================================
# apps.py — App: clientes
# Configuración de la aplicación Django para el módulo de clientes.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.clientes' en INSTALLED_APPS de config/settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# ClientesConfig
# Clase de configuración de la app 'clientes'.
# Define el campo auto-incrementable por defecto y el nombre de la app.
# -----------------------------------------------------------------------------
class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # PK BigInt (64 bits) por defecto en todos los modelos
    name = 'apps.clientes'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS