# =============================================================================
# apps.py — App: reportes
# NOTA: Este archivo contiene un formulario Django (ReporteFiltroForm) en lugar
# de la clase AppConfig estándar. El formulario define las opciones de filtro
# por estado para el reporte de solicitudes.
#
# ReporteFiltroForm NO está siendo usado actualmente en las vistas: los filtros
# se leen directamente de request.GET en obtener_solicitudes_filtradas().
# Este formulario es un artefacto de una implementación anterior o futura.
# =============================================================================

from django import forms


# -----------------------------------------------------------------------------
# ReporteFiltroForm
# Formulario de filtro de estado para el reporte de solicitudes.
# Define tres opciones: todos (APROBADA + RECHAZADA), aceptado, rechazado.
# Actualmente no se instancia ni se pasa al template desde ninguna vista.
# Los filtros están implementados directamente vía request.GET en views.py.
# -----------------------------------------------------------------------------
class ReporteFiltroForm(forms.Form):
    ESTADO_CHOICES = (
        ('todos',     'Aceptados y Rechazados'),  # Filtra estado__in=['APROBADA','RECHAZADA']
        ('aceptado',  'Aceptados'),               # Filtra estado='APROBADA'
        ('rechazado', 'Rechazados'),              # Filtra estado='RECHAZADA'
    )

    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        label='Filtrar por estado',
        initial='todos'
    )