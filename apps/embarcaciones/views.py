# =============================================================================
# views.py — App: embarcaciones
# Archivo de vistas de la app embarcaciones. No contiene vistas propias.
#
# La creación de embarcaciones ocurre en apps/publico/views.py: cuando
# alguien envía el formulario público de solicitud se hace get_or_create
# sobre Embarcacion usando cliente + nombre_bote como clave compuesta.
#
# La consulta y edición de embarcaciones se hace desde el admin (/admin/).
# No se implementó un CRUD propio para embarcaciones en este proyecto.
# =============================================================================

from django.shortcuts import render                               # Sin uso actual
from django.contrib.auth.decorators import login_required         # Sin uso actual