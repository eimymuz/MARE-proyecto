from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from apps.solicitudes.models import Solicitud


def reporte_solicitudes(request):
    estado = request.GET.get('estado', 'todos')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

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

    # filtro por estado
    if estado == 'aceptado':
        solicitudes = solicitudes.filter(estado='APROBADA')
    elif estado == 'rechazado':
        solicitudes = solicitudes.filter(estado='RECHAZADA')
    else:
        solicitudes = solicitudes.filter(estado__in=['APROBADA', 'RECHAZADA'])

    solicitudes = list(solicitudes)

    # calcular fecha de resolución
    for s in solicitudes:
        historial = (
            s.historial.filter(
                estado_nuevo__in=['APROBADA', 'RECHAZADA']
            )
            .order_by('-fecha_cambio')
            .first()
        )
        s.fecha_resolucion = historial.fecha_cambio if historial else None

    # 🔥 filtro por mes
    if mes:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.month == int(mes)
        ]

    # 🔥 filtro por año
    if anio:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.year == int(anio)
        ]

    total = len(solicitudes)

    # listas para selects
    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    anios = range(2026, timezone.now().year + 5)

    context = {
        'solicitudes': solicitudes,
        'estado': estado,
        'mes': mes,
        'anio': anio,
        'meses': meses,
        'anios': anios,
        'total': total,
    }

    return render(request, 'reporte/reporte.html', context)


def reporte_solicitudes_pdf(request):
    estado = request.GET.get('estado', 'todos')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

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
    else:
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

    # filtros en PDF también
    if mes:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.month == int(mes)
        ]

    if anio:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.year == int(anio)
        ]

    total = len(solicitudes)

    html_string = render_to_string(
        'reporte/reporte_pdf.html',
        {
            'solicitudes': solicitudes,
            'estado': estado,
            'mes': mes,
            'anio': anio,
            'total': total,
            'fecha_descarga': timezone.localtime(),
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_solicitudes.pdf"'

    HTML(string=html_string).write_pdf(response)

    return response