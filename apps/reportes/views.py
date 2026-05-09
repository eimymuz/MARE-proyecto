from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count
from weasyprint import HTML

from apps.solicitudes.models import Solicitud


def calcular_fecha_resolucion(solicitud):
    historial = (
        solicitud.historial.filter(
            estado_nuevo__in=['APROBADA', 'RECHAZADA', 'COMPLETADA']
        )
        .order_by('-fecha_cambio')
        .first()
    )

    return historial.fecha_cambio if historial else None


def obtener_estadisticas():
    total_estadisticas = Solicitud.objects.count()

    completadas = Solicitud.objects.filter(
        estado='COMPLETADA'
    ).count()

    rechazadas = Solicitud.objects.filter(
        estado='RECHAZADA'
    ).count()

    aprobadas = Solicitud.objects.filter(
        estado='APROBADA'
    ).count()

    pendientes = Solicitud.objects.filter(
        estado='PENDIENTE'
    ).count()

    en_espera = Solicitud.objects.filter(
        estado='EN_ESPERA'
    ).count()

    en_proceso = pendientes + en_espera + aprobadas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas / total_estadisticas) * 100, 2)
        porcentaje_proceso = round((en_proceso / total_estadisticas) * 100, 2)
        porcentaje_rechazadas = round((rechazadas / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = 0
        porcentaje_proceso = 0
        porcentaje_rechazadas = 0

    return {
        'total_estadisticas': total_estadisticas,
        'completadas': completadas,
        'rechazadas': rechazadas,
        'aprobadas': aprobadas,
        'pendientes': pendientes,
        'en_espera': en_espera,
        'en_proceso': en_proceso,
        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso': porcentaje_proceso,
        'porcentaje_rechazadas': porcentaje_rechazadas,
    }


def obtener_solicitudes_filtradas(request):
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
    elif estado == 'completado':
        solicitudes = solicitudes.filter(estado='COMPLETADA')
    elif estado == 'proceso':
        solicitudes = solicitudes.filter(
            estado__in=['PENDIENTE', 'EN_ESPERA', 'APROBADA']
        )
    else:
        solicitudes = solicitudes.filter(
            estado__in=['APROBADA', 'RECHAZADA']
        )

    solicitudes = list(solicitudes)

    for solicitud in solicitudes:
        solicitud.fecha_resolucion = calcular_fecha_resolucion(solicitud)

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

    return solicitudes, estado, mes, anio


def reporte_solicitudes(request):
    solicitudes, estado, mes, anio = obtener_solicitudes_filtradas(request)

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
        'total': len(solicitudes),
    }

    return render(request, 'reporte/reporte.html', context)


def reporte_solicitudes_pdf(request):
    solicitudes, estado, mes, anio = obtener_solicitudes_filtradas(request)

    html_string = render_to_string(
        'reporte/reporte_pdf.html',
        {
            'solicitudes': solicitudes,
            'estado': estado,
            'mes': mes,
            'anio': anio,
            'total': len(solicitudes),
            'fecha_descarga': timezone.localtime(),
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_solicitudes.pdf"'

    HTML(string=html_string).write_pdf(response)

    return response


def estadisticas_solicitudes(request):
    estadisticas = obtener_estadisticas()

    solicitudes_mes = (
        Solicitud.objects
        .values('fecha_solicitud__month')
        .annotate(total=Count('id'))
        .order_by('fecha_solicitud__month')
    )

    meses = [
        'Enero', 'Febrero', 'Marzo',
        'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre',
        'Octubre', 'Noviembre', 'Diciembre'
    ]

    labels = []
    data = []

    for item in solicitudes_mes:
        mes_num = item['fecha_solicitud__month']

        if mes_num:
            labels.append(meses[mes_num - 1])
            data.append(item['total'])

    context = {
        **estadisticas,
        'labels': labels,
        'data': data,
    }

    return render(request, 'reporte/estadisticas.html', context)


def reporte_estadisticas_pdf(request):
    estadisticas = obtener_estadisticas()

    html_string = render_to_string(
        'reporte/reporte_estadisticas_pdf.html',
        {
            **estadisticas,
            'fecha_descarga': timezone.localtime(),
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_estadisticas.pdf"'

    HTML(string=html_string).write_pdf(response)

    return response