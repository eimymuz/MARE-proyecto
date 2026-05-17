import io
import base64
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from weasyprint import HTML

from apps.solicitudes.models import Solicitud


# ==========================================
# GRÁFICA: SOLICITUDES POR MES
# ==========================================

def generar_grafica_mensual(solicitudes):
    solicitudes_mes = (
        solicitudes
        .values('fecha_solicitud__month')
        .annotate(total=Count('id'))
        .order_by('fecha_solicitud__month')
    )

    meses = [
        'Ene', 'Feb', 'Mar', 'Abr',
        'May', 'Jun', 'Jul', 'Ago',
        'Sep', 'Oct', 'Nov', 'Dic'
    ]

    conteos = [0] * 12

    for item in solicitudes_mes:
        mes = item['fecha_solicitud__month']

        if mes:
            conteos[mes - 1] = item['total']

    fig, ax = plt.subplots(figsize=(10, 4))

    barras = ax.bar(
        meses,
        conteos,
        color='#08213d',
        width=0.55
    )

    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')

    ax.tick_params(colors='#475569')
    ax.set_ylabel('Solicitudes', color='#475569')

    maximo = max(conteos) if conteos else 0
    ax.set_ylim(0, maximo + 1 if maximo > 0 else 1)

    for barra in barras:
        altura = barra.get_height()

        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + 0.05,
            str(int(altura)),
            ha='center',
            va='bottom',
            fontsize=9,
            color='#08213d'
        )

    plt.tight_layout()

    buffer = io.BytesIO()

    plt.savefig(
        buffer,
        format='png',
        dpi=200,
        bbox_inches='tight'
    )

    buffer.seek(0)

    grafica = base64.b64encode(buffer.getvalue()).decode('utf-8')

    buffer.close()
    plt.close(fig)

    return grafica


# ==========================================
# GRÁFICA: DISTRIBUCIÓN POR ESTADO
# ==========================================

def generar_grafica_estados(completadas, en_proceso, rechazadas):
    valores = [
        completadas,
        en_proceso,
        rechazadas
    ]

    colores = [
        '#22c55e',
        '#eab308',
        '#ef4444'
    ]

    total = sum(valores)

    if total == 0:
        valores = [1]
        colores = ['#cbd5e1']

    fig, ax = plt.subplots(figsize=(4.2, 4.2))

    ax.pie(
        valores,
        labels=None,
        colors=colores,
        startangle=90,
        counterclock=False,
        wedgeprops={
            'width': 0.36,
            'edgecolor': 'white',
            'linewidth': 3
        }
    )

    if total > 0:
        ax.text(
            0,
            0.08,
            str(total),
            ha='center',
            va='center',
            fontsize=24,
            fontweight='bold',
            color='#08213d'
        )

        ax.text(
            0,
            -0.15,
            'Total',
            ha='center',
            va='center',
            fontsize=11,
            fontweight='bold',
            color='#475569'
        )
    else:
        ax.text(
            0,
            -1.15,
            'Sin datos',
            ha='center',
            va='center',
            fontsize=10,
            color='#475569'
        )

    ax.set(aspect='equal')
    ax.axis('off')

    plt.tight_layout(pad=0.2)

    buffer = io.BytesIO()

    plt.savefig(
        buffer,
        format='png',
        dpi=200,
        bbox_inches='tight',
        transparent=False
    )

    buffer.seek(0)

    grafica = base64.b64encode(buffer.getvalue()).decode('utf-8')

    buffer.close()
    plt.close(fig)

    return grafica


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

    completadas = Solicitud.objects.filter(estado='COMPLETADA').count()
    rechazadas = Solicitud.objects.filter(estado='RECHAZADA').count()
    aprobadas = Solicitud.objects.filter(estado='APROBADA').count()
    pendientes = Solicitud.objects.filter(estado='PENDIENTE').count()
    en_espera = Solicitud.objects.filter(estado='EN_ESPERA').count()

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
    )

    if estado == 'aceptado':
        solicitudes = solicitudes.filter(estado='APROBADA')
    elif estado == 'rechazado':
        solicitudes = solicitudes.filter(estado='RECHAZADA')
    elif estado == 'completado':
        solicitudes = solicitudes.filter(estado='COMPLETADA')
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

    solicitudes.sort(
        key=lambda s: s.fecha_resolucion or timezone.datetime.min.replace(
            tzinfo=timezone.get_current_timezone()
        ),
        reverse=True
    )

    return solicitudes, estado, mes, anio


def reporte_solicitudes(request):
    solicitudes, estado, mes, anio = obtener_solicitudes_filtradas(request)

    paginator = Paginator(solicitudes, 15)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    anios = range(2026, timezone.now().year + 5)

    context = {
        'solicitudes': page_obj,
        'page_obj': page_obj,
        'estado': estado,
        'mes': mes,
        'anio': anio,
        'meses': meses,
        'anios': anios,
        'total': paginator.count,
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

    HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf(response)

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

    if mes:
        mes_actual = int(mes)
    else:
        mes_actual = timezone.now().month

    if anio:
        anio_actual = int(anio)
    else:
        anio_actual = timezone.now().year

    if mes_actual == 1:
        mes_anterior = 12
        anio_anterior = anio_actual - 1
    else:
        mes_anterior = mes_actual - 1
        anio_anterior = anio_actual

    total_mes_actual = Solicitud.objects.filter(
        fecha_solicitud__month=mes_actual,
        fecha_solicitud__year=anio_actual
    ).count()

    total_mes_anterior = Solicitud.objects.filter(
        fecha_solicitud__month=mes_anterior,
        fecha_solicitud__year=anio_anterior
    ).count()

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

    aprobadas = solicitudes.filter(
        estado__in=['APROBADA', 'COMPLETADA']
    ).count()

    aprobadas_directas = solicitudes.filter(estado='APROBADA').count()
    completadas = solicitudes.filter(estado='COMPLETADA').count()
    rechazadas = solicitudes.filter(estado='RECHAZADA').count()
    pendientes = solicitudes.filter(estado='PENDIENTE').count()
    en_espera = solicitudes.filter(estado='EN_ESPERA').count()

    aprobadas = aprobadas_directas + completadas

    en_proceso = pendientes + en_espera + aprobadas_directas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas / total_estadisticas) * 100, 2)
        porcentaje_proceso = round((en_proceso / total_estadisticas) * 100, 2)
        porcentaje_rechazadas = round((rechazadas / total_estadisticas) * 100, 2)
        tasa_aprobacion = round((aprobadas / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = 0
        porcentaje_proceso = 0
        porcentaje_rechazadas = 0
        tasa_aprobacion = 0

    top_embarcaciones = (
        solicitudes
        .values(
            'embarcacion__nombre_bote',
            'embarcacion__tipo_barco__tipo_barco'
        )
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
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

    grafica_mensual = generar_grafica_mensual(solicitudes)

    grafica_estados = generar_grafica_estados(
        completadas,
        en_proceso,
        rechazadas
    )

    meses_dict = {
        '1': 'Enero',
        '2': 'Febrero',
        '3': 'Marzo',
        '4': 'Abril',
        '5': 'Mayo',
        '6': 'Junio',
        '7': 'Julio',
        '8': 'Agosto',
        '9': 'Septiembre',
        '10': 'Octubre',
        '11': 'Noviembre',
        '12': 'Diciembre',
    }

    context = {
        'total_estadisticas': total_estadisticas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
        'completadas': completadas,
        'pendientes': pendientes,
        'en_espera': en_espera,
        'en_proceso': en_proceso,

        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso': porcentaje_proceso,
        'porcentaje_rechazadas': porcentaje_rechazadas,
        'tasa_aprobacion': tasa_aprobacion,

        'top_embarcaciones': top_embarcaciones,
        'estancias_tipo_data': estancias_tipo_data,

        'grafica_mensual': grafica_mensual,
        'grafica_estados': grafica_estados,

        'mes': meses_dict.get(mes, 'Todos'),
        'anio': anio if anio else 'Todos',
        'fecha_descarga': timezone.localtime(),
    }

    html_string = render_to_string(
        'reporte/reporte_estadisticas_pdf.html',
        context
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_estadisticas.pdf"'

    HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf(response)

    return response