from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.solicitudes.models import Solicitud


def reporte_solicitudes(request):
    estado = request.GET.get('estado', 'todos')

    solicitudes = (
        Solicitud.objects.select_related(
            'embarcacion',
            'embarcacion__cliente',
            'embarcacion__tipo_barco'
        )
        .prefetch_related('historial')
        .all()
        .order_by('-fecha_solicitud')
    )

    if estado == 'aceptado':
        solicitudes = solicitudes.filter(estado='APROBADA')
    elif estado == 'rechazado':
        solicitudes = solicitudes.filter(estado='RECHAZADA')
    elif estado == 'todos':
        solicitudes = solicitudes.filter(estado__in=['APROBADA', 'RECHAZADA'])

    solicitudes = list(solicitudes)

    for s in solicitudes:
        historial = (
            s.historial.filter(
                estado_nuevo__in=['APROBADA', 'RECHAZADA']
            )
            .order_by('-fecha_cambio')
            .first()
        )
        s.fecha_resolucion = historial.fecha_cambio if historial else None

    total = len(solicitudes)

    context = {
        'solicitudes': solicitudes,
        'estado': estado,
        'total': total,
    }

    return render(request, 'reporte/reporte.html', context)


def reporte_solicitudes_pdf(request):
    estado = request.GET.get('estado', 'todos')

    solicitudes = (
        Solicitud.objects.select_related(
            'embarcacion',
            'embarcacion__cliente',
            'embarcacion__tipo_barco'
        )
        .prefetch_related('historial')
        .all()
        .order_by('-fecha_solicitud')
    )

    if estado == 'aceptado':
        solicitudes = solicitudes.filter(estado='APROBADA')
    elif estado == 'rechazado':
        solicitudes = solicitudes.filter(estado='RECHAZADA')
    elif estado == 'todos':
        solicitudes = solicitudes.filter(estado__in=['APROBADA', 'RECHAZADA'])

    solicitudes = list(solicitudes)

    for s in solicitudes:
        historial = (
            s.historial.filter(
                estado_nuevo__in=['APROBADA', 'RECHAZADA']
            )
            .order_by('-fecha_cambio')
            .first()
        )
        s.fecha_resolucion = historial.fecha_cambio if historial else None

    total = len(solicitudes)

    html_string = render_to_string(
        'reporte/reporte_pdf.html',
        {
            'solicitudes': solicitudes,
            'estado': estado,
            'total': total,
            'fecha_descarga': timezone.localtime(),
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_solicitudes.pdf"'

    HTML(string=html_string).write_pdf(response)

    return response