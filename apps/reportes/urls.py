from django.urls import path
from .views import reporte_solicitudes, reporte_solicitudes_pdf

urlpatterns = [
    path('', reporte_solicitudes, name='reporte_solicitudes'),
    path('pdf/', reporte_solicitudes_pdf, name='reporte_solicitudes_pdf'),
]