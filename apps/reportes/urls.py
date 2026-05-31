# =============================================================================
# urls.py — App: reportes
# Define las rutas de la app reportes. Incluido en config/urls.py bajo el
# prefijo /reportes/.
#
# Rutas resultantes:
#   GET /reportes/                → views.reporte_solicitudes      (name='reporte_solicitudes')
#   GET /reportes/estadisticas/   → views.estadisticas_solicitudes (name='estadisticas_solicitudes')
#   GET /reportes/pdf/            → views.reporte_solicitudes_pdf  (name='reporte_solicitudes_pdf')
#   GET /reportes/estadisticas/pdf/ → views.reporte_estadisticas_pdf (name='reporte_estadisticas_pdf')
#
# Consumidores:
#   - templates/components/navbar.html     (enlaces "Reporte" y "Estadísticas")
#   - templates/reporte/reporte.html       (botón "Descargar PDF" → reporte_solicitudes_pdf)
#   - templates/reporte/estadisticas.html  (botón "Descargar PDF" → reporte_estadisticas_pdf)
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.reporte_solicitudes, name='reporte_solicitudes'),

    # Página de estadísticas operativas con gráficas CSS y métricas de crecimiento
    path(
        'estadisticas/',
        views.estadisticas_solicitudes,
        name='estadisticas_solicitudes'
    ),

    # Descarga del reporte de solicitudes en formato PDF (weasyprint)
    path(
        'pdf/',
        views.reporte_solicitudes_pdf,
        name='reporte_solicitudes_pdf'
    ),

    # Descarga de las estadísticas con gráficas matplotlib en formato PDF
    path(
        'estadisticas/pdf/',
        views.reporte_estadisticas_pdf,
        name='reporte_estadisticas_pdf'
    ),
]