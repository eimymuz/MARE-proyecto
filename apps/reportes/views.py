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
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

    solicitudes = Solicitud.objects.select_related(
        'embarcacion',
        'embarcacion__tipo_barco'
    ).all()

    if mes:
        solicitudes = solicitudes.filter(fecha_solicitud__month=int(mes))

    if anio:
        solicitudes = solicitudes.filter(fecha_solicitud__year=int(anio))

    total_estadisticas = solicitudes.count()

    aprobadas = solicitudes.filter(estado='APROBADA').count()
    rechazadas = solicitudes.filter(estado='RECHAZADA').count()
    completadas = solicitudes.filter(estado='COMPLETADA').count()
    pendientes = solicitudes.filter(estado='PENDIENTE').count()
    en_espera = solicitudes.filter(estado='EN_ESPERA').count()

    en_proceso = pendientes + en_espera + aprobadas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas / total_estadisticas) * 100, 2)
        porcentaje_proceso = round((en_proceso / total_estadisticas) * 100, 2)
        porcentaje_rechazadas = round((rechazadas / total_estadisticas) * 100, 2)
        tasa_aprobacion = round(((aprobadas + completadas) / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = 0
        porcentaje_proceso = 0
        porcentaje_rechazadas = 0
        tasa_aprobacion = 0

    solicitudes_mes = (
        solicitudes
        .values('fecha_solicitud__month')
        .annotate(total=Count('id'))
        .order_by('fecha_solicitud__month')
    )

    meses_cortos = [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
    ]

    conteo_por_mes = {i: 0 for i in range(1, 13)}

    for item in solicitudes_mes:
        mes_num = item['fecha_solicitud__month']
        if mes_num:
            conteo_por_mes[mes_num] = item['total']

    maximo_mes = max(conteo_por_mes.values())

    solicitudes_mes_data = []

    for numero_mes in range(1, 13):
        total_mes = conteo_por_mes[numero_mes]

        porcentaje = 0
        if maximo_mes > 0:
            porcentaje = round((total_mes / maximo_mes) * 100, 2)

        solicitudes_mes_data.append({
            'mes': meses_cortos[numero_mes - 1],
            'total': total_mes,
            'porcentaje': porcentaje,
            'activo': total_mes > 0,
        })

    top_embarcaciones = (
        solicitudes
        .values(
            'embarcacion__nombre_bote',
            'embarcacion__tipo_barco__tipo_barco'
        )
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    estancias_tipo = (
        solicitudes
        .values('embarcacion__tipo_barco__tipo_barco')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    total_tipo = sum(item['total'] for item in estancias_tipo)

    estancias_tipo_data = []

    for item in estancias_tipo:
        porcentaje = 0

        if total_tipo > 0:
            porcentaje = round((item['total'] / total_tipo) * 100, 2)

        estancias_tipo_data.append({
            'tipo': item['embarcacion__tipo_barco__tipo_barco'] or 'Sin tipo',
            'total': item['total'],
            'porcentaje': porcentaje,
        })

    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    anios = range(2026, timezone.now().year + 5)
    mes_actual = timezone.now().month
    mes_anterior = mes_actual - 1 if mes_actual > 1 else 12

    total_mes_actual = conteo_por_mes.get(mes_actual, 0)
    total_mes_anterior = conteo_por_mes.get(mes_anterior, 0)

    crecimiento_mensual = 0
    tipo_crecimiento = 'neutral'

    if total_mes_anterior > 0:
        crecimiento_mensual = round(
            ((total_mes_actual - total_mes_anterior) / total_mes_anterior) * 100,
            2
        )

        if crecimiento_mensual > 0:
            tipo_crecimiento = 'positivo'
        elif crecimiento_mensual < 0:
            tipo_crecimiento = 'negativo'
    else:
        if total_mes_actual > 0:
            crecimiento_mensual = 100
            tipo_crecimiento = 'positivo'

    context = {
        'mes': mes,
        'anio': anio,
        'meses': meses,
        'anios': anios,

        'crecimiento_mensual': crecimiento_mensual,
        'tipo_crecimiento': tipo_crecimiento,
        'total_mes_actual': total_mes_actual,
        'total_mes_anterior': total_mes_anterior,

        'total_estadisticas': total_estadisticas,
        'total_solicitudes': total_estadisticas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
        'completadas': completadas,
        'pendientes': pendientes,
        'en_espera': en_espera,
        'en_proceso': en_proceso,
        'solicitudes_aprobadas': aprobadas + completadas,
        'tasa_aprobacion': tasa_aprobacion,

        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso': porcentaje_proceso,
        'porcentaje_rechazadas': porcentaje_rechazadas,

        'solicitudes_mes_data': solicitudes_mes_data,
        'top_embarcaciones': top_embarcaciones,
        'estancias_tipo_data': estancias_tipo_data,
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