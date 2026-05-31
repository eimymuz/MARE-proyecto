# =============================================================================
# apps.py — App: solicitudes
# Configuración de la aplicación Django para el módulo de solicitudes.
# Django la lee al arrancar para registrar la app dentro del proyecto
# (entrada 'apps.solicitudes' en INSTALLED_APPS de config/settings.py).
#
# Esta app define los dos modelos centrales del sistema: Solicitud y
# SolicitudHistorial, que son referenciados por casi todas las demás apps.
# =============================================================================

from django.apps import AppConfig


# -----------------------------------------------------------------------------
# SolicitudesConfig
# Clase de configuración de la app 'solicitudes'.
# -----------------------------------------------------------------------------
class SolicitudesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # PK BigInt (64 bits) para Solicitud y SolicitudHistorial
    name = 'apps.solicitudes'  # Ruta Python de la app; debe coincidir con la entrada en INSTALLED_APPS