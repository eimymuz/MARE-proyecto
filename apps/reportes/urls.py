from django.urls import path
from . import views

urlpatterns = [
    path('', views.reporte_solicitudes, name='reporte_solicitudes'),

     # ===== NUEVA PAGINA DE ESTADISTICAS =====
    path(
        'estadisticas/',
        views.estadisticas_solicitudes,
        name='estadisticas_solicitudes'
    ),

    # ===== PDF REPORTES =====
    path(
        'pdf/',
        views.reporte_solicitudes_pdf,
        name='reporte_solicitudes_pdf'
    ),

    # ===== PDF ESTADISTICAS =====
    path(
        'estadisticas/pdf/',
        views.reporte_estadisticas_pdf,
        name='reporte_estadisticas_pdf'
    ),
]