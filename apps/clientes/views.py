# =============================================================================
# views.py — App: clientes
# Archivo de vistas de la app clientes. No contiene vistas propias.
#
# La creación de clientes ocurre en apps/publico/views.py: cuando alguien
# envía el formulario público de solicitud se hace get_or_create sobre
# Cliente usando el email como clave de unicidad.
#
# La consulta y edición de clientes se hace desde el admin de Django (/admin/).
# No se implementó un CRUD propio para clientes en este proyecto.
# =============================================================================

from django.shortcuts import render  # Importado por defecto; sin uso actual