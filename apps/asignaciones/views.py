# =============================================================================
# views.py — App: asignaciones
# Archivo de vistas de la app asignaciones. Actualmente no contiene vistas
# propias: toda la lógica de creación y gestión de asignaciones está
# implementada en apps/solicitudes/views.py, que importa los modelos
# Asignacion y Administrador directamente desde esta app.
# =============================================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required  # Decorador disponible para proteger futuras vistas