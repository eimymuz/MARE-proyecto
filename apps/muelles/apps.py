# =============================================================================
# apps.py — App: muelles
# Configuración de la aplicación Django para el módulo de muelles.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.muelles' en INSTALLED_APPS de config/settings.py).
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# MuellesConfig
# Clase de configuración de la app 'muelles'.
# Define los cuatro modelos de infraestructura física de la marina:
# Muelle, Espacio, ZonaTierra y EtiquetaMuelle.
# -----------------------------------------------------------------------------
class MuellesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # PK BigInt (64 bits) para todos los modelos
    name = 'apps.muelles'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS