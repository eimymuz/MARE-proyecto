from django.urls import path
from . import views

urlpatterns = [
    path('', views.reporte_solicitudes, name='reporte_solicitudes'),

    path(
        'pdf/',
        views.reporte_solicitudes_pdf,
        name='reporte_solicitudes_pdf'
    ),

    path(
        'estadisticas/pdf/',
        views.reporte_estadisticas_pdf,
        name='reporte_estadisticas_pdf'
    ),
]