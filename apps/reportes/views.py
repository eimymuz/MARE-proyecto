# =============================================================================
# views.py — App: reportes
# Genera el reporte de solicitudes resueltas, la página de estadísticas
# operativas y sus versiones descargables en PDF.
#
# Dependencias externas:
#   - matplotlib (Agg backend, sin GUI) → genera gráficas como imágenes PNG
#   - weasyprint                        → convierte HTML a PDF para descargas
#
# Vistas (registradas en urls.py de esta app):
#   reporte_solicitudes      GET /reportes/                → reporte/reporte.html
#   reporte_solicitudes_pdf  GET /reportes/pdf/            → descarga PDF
#   estadisticas_solicitudes GET /reportes/estadisticas/   → reporte/estadisticas.html
#   reporte_estadisticas_pdf GET /reportes/estadisticas/pdf/ → descarga PDF
#
# Funciones auxiliares (no son vistas):
#   generar_grafica_mensual   → imagen base64 de barras por mes
#   generar_grafica_estados   → imagen base64 de dona por estado
#   calcular_fecha_resolucion → fecha del último cambio de estado final en el historial
#   obtener_estadisticas      → conteos globales por estado (sin uso activo en vistas actuales)
#   obtener_solicitudes_filtradas → queryset + anotación de fecha_resolucion + filtros GET
#
# Modelo usado: apps.solicitudes.Solicitud (+ relación historial → SolicitudHistorial)
# =============================================================================

import io
import base64
import matplotlib

# Agg: backend sin GUI de matplotlib; necesario en servidores Django sin pantalla
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string  # Para renderizar HTML que luego weasyprint convierte a PDF
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from weasyprint import HTML  # Convierte HTML+CSS a PDF; base_url permite resolver rutas estáticas

from apps.solicitudes.models import Solicitud


# =============================================================================
# generar_grafica_mensual
# Genera un gráfico de barras (matplotlib) con la cantidad de solicitudes
# por mes del queryset recibido. Retorna la imagen codificada en base64
# para incrustarla directamente en el HTML del PDF como <img src="data:...">
#
# Parámetros:
#   solicitudes → queryset de Solicitud (puede estar filtrado por año)
#
# Retorna: string base64 de la imagen PNG (200 dpi, fondo blanco)
# Usado en: reporte_estadisticas_pdf → context['grafica_mensual']
#           → template reporte/reporte_estadisticas_pdf.html
# =============================================================================
def generar_grafica_mensual(solicitudes):
    # Agrupa el queryset por mes y cuenta cuántas solicitudes hay en cada uno
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

    conteos = [0] * 12  # Inicializa en 0 los 12 meses; se rellenan con los datos de la BD

    for item in solicitudes_mes:
        mes = item['fecha_solicitud__month']
        if mes:
            conteos[mes - 1] = item['total']  # mes-1 porque los índices de lista van de 0 a 11

    fig, ax = plt.subplots(figsize=(10, 4))

    barras = ax.bar(meses, conteos, color='#08213d', width=0.55)

    # Estilo visual: fondo blanco, sin bordes superior y derecho
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.tick_params(colors='#475569')
    ax.set_ylabel('Solicitudes', color='#475569')

    maximo = max(conteos) if conteos else 0
    ax.set_ylim(0, maximo + 1 if maximo > 0 else 1)  # +1 para que la barra más alta no toque el tope

    # Etiqueta numérica encima de cada barra
    for barra in barras:
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + 0.05,
            str(int(altura)),
            ha='center', va='bottom', fontsize=9, color='#08213d'
        )

    plt.tight_layout()

    # Serializa la figura a PNG en memoria y la codifica en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
    buffer.seek(0)
    grafica = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close(fig)  # Libera memoria; sin esto matplotlib acumula figuras abiertas

    return grafica


# =============================================================================
# generar_grafica_estados
# Genera un gráfico de dona (pie con hueco) con la distribución de solicitudes
# por grupo de estado: completadas (verde), en proceso (amarillo), rechazadas (rojo).
# Si no hay datos, muestra un círculo gris con texto "Sin datos".
# Retorna la imagen codificada en base64.
#
# Parámetros:
#   completadas, en_proceso, rechazadas → enteros con conteos por grupo
#
# Usado en: reporte_estadisticas_pdf → context['grafica_estados']
#           → template reporte/reporte_estadisticas_pdf.html
# =============================================================================
def generar_grafica_estados(completadas, en_proceso, rechazadas):
    valores = [completadas, en_proceso, rechazadas]
    colores = ['#22c55e', '#eab308', '#ef4444']

    total = sum(valores)

    # Si no hay datos reales, muestra un segmento gris neutro en lugar de un error
    if total == 0:
        valores = [1]
        colores = ['#cbd5e1']

    fig, ax = plt.subplots(figsize=(4.2, 4.2))

    # wedgeprops.width=0.36 crea el hueco central de la dona
    ax.pie(
        valores, labels=None, colors=colores,
        startangle=90, counterclock=False,
        wedgeprops={'width': 0.36, 'edgecolor': 'white', 'linewidth': 3}
    )

    # Texto central: total numérico y etiqueta "Total"
    if total > 0:
        ax.text(0, 0.08, str(total), ha='center', va='center',
                fontsize=24, fontweight='bold', color='#08213d')
        ax.text(0, -0.15, 'Total', ha='center', va='center',
                fontsize=11, fontweight='bold', color='#475569')
    else:
        ax.text(0, -1.15, 'Sin datos', ha='center', va='center',
                fontsize=10, color='#475569')

    ax.set(aspect='equal')
    ax.axis('off')
    plt.tight_layout(pad=0.2)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', transparent=False)
    buffer.seek(0)
    grafica = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close(fig)

    return grafica


# =============================================================================
# calcular_fecha_resolucion
# Devuelve la fecha del último cambio de estado "final" (APROBADA, RECHAZADA
# o COMPLETADA) de una solicitud, consultando su historial de cambios.
# Retorna None si la solicitud no tiene historial de estados finales.
#
# Se llama sobre cada solicitud en obtener_solicitudes_filtradas() para
# adjuntar .fecha_resolucion como atributo dinámico a cada objeto.
# Esa fecha se usa para filtrar por mes/año y para ordenar el listado.
#
# Requiere que solicitud.historial esté prefetcheado para evitar N+1.
# =============================================================================
def calcular_fecha_resolucion(solicitud):
    historial = (
        # .historial es el related_name de SolicitudHistorial.solicitud (FK)
        solicitud.historial.filter(
            estado_nuevo__in=['APROBADA', 'RECHAZADA', 'COMPLETADA']
        )
        .order_by('-fecha_cambio')  # El más reciente primero
        .first()
    )
    return historial.fecha_cambio if historial else None


# =============================================================================
# obtener_estadisticas
# Calcula conteos y porcentajes globales de todas las solicitudes del sistema.
# Función auxiliar disponible pero no usada actualmente en ninguna vista activa;
# las vistas calculan sus propios conteos con filtros de mes/año aplicados.
# =============================================================================
def obtener_estadisticas():
    total_estadisticas = Solicitud.objects.count()

    completadas = Solicitud.objects.filter(estado='COMPLETADA').count()
    rechazadas  = Solicitud.objects.filter(estado='RECHAZADA').count()
    aprobadas   = Solicitud.objects.filter(estado='APROBADA').count()
    pendientes  = Solicitud.objects.filter(estado='PENDIENTE').count()
    en_espera   = Solicitud.objects.filter(estado='EN_ESPERA').count()

    # en_proceso agrupa las que aún no han terminado su ciclo de vida
    en_proceso = pendientes + en_espera + aprobadas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas / total_estadisticas) * 100, 2)
        porcentaje_proceso     = round((en_proceso  / total_estadisticas) * 100, 2)
        porcentaje_rechazadas  = round((rechazadas  / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = porcentaje_proceso = porcentaje_rechazadas = 0

    return {
        'total_estadisticas': total_estadisticas,
        'completadas': completadas, 'rechazadas': rechazadas,
        'aprobadas': aprobadas, 'pendientes': pendientes,
        'en_espera': en_espera, 'en_proceso': en_proceso,
        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso': porcentaje_proceso,
        'porcentaje_rechazadas': porcentaje_rechazadas,
    }


# =============================================================================
# obtener_solicitudes_filtradas
# Función auxiliar compartida entre reporte_solicitudes y reporte_solicitudes_pdf.
# Aplica filtros GET (estado, mes, año), anota cada solicitud con su
# fecha_resolucion y ordena el resultado de más reciente a más antiguo.
#
# Parámetros GET leídos:
#   estado → 'todos' | 'aceptado' | 'rechazado' | 'completado'
#   mes    → número de mes (1-12) para filtrar por fecha_resolucion.month
#   anio   → año para filtrar por fecha_resolucion.year
#
# Nota: el filtro de mes/año se aplica en Python (no en SQL) porque
# fecha_resolucion es un atributo calculado a partir del historial,
# no un campo de la base de datos.
#
# Retorna: (solicitudes: list, estado: str, mes: str, anio: str)
# =============================================================================
def obtener_solicitudes_filtradas(request):
    estado = request.GET.get('estado', 'todos')
    mes    = request.GET.get('mes', '')
    anio   = request.GET.get('anio', '')

    # select_related evita N+1 al acceder a embarcacion, cliente y tipo_barco en templates
    # prefetch_related('historial') evita N+1 en calcular_fecha_resolucion()
    solicitudes = (
        Solicitud.objects.select_related(
            'embarcacion',
            'embarcacion__cliente',
            'embarcacion__tipo_barco'
        )
        .prefetch_related('historial')
        .all()
    )

    # El reporte solo muestra solicitudes con estado final (resueltas).
    # 'todos' = APROBADA + RECHAZADA (las más relevantes para el reporte de gestión)
    if estado == 'aceptado':
        solicitudes = solicitudes.filter(estado='APROBADA')
    elif estado == 'rechazado':
        solicitudes = solicitudes.filter(estado='RECHAZADA')
    elif estado == 'completado':
        solicitudes = solicitudes.filter(estado='COMPLETADA')
    else:
        solicitudes = solicitudes.filter(estado__in=['APROBADA', 'RECHAZADA'])

    # Evalúa el queryset a lista para poder agregar el atributo .fecha_resolucion
    # (los querysets de Django no permiten agregar atributos dinámicos por fila)
    solicitudes = list(solicitudes)

    for solicitud in solicitudes:
        # Agrega fecha_resolucion como atributo dinámico; disponible luego en templates
        solicitud.fecha_resolucion = calcular_fecha_resolucion(solicitud)

    # Filtro de mes en Python: solo aplica si el filtro está presente
    if mes:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.month == int(mes)
        ]

    # Filtro de año en Python
    if anio:
        solicitudes = [
            s for s in solicitudes
            if s.fecha_resolucion and s.fecha_resolucion.year == int(anio)
        ]

    # Ordena de más reciente a más antiguo.
    # Las solicitudes sin fecha_resolucion van al final (timezone.datetime.min)
    solicitudes.sort(
        key=lambda s: s.fecha_resolucion or timezone.datetime.min.replace(
            tzinfo=timezone.get_current_timezone()
        ),
        reverse=True
    )

    return solicitudes, estado, mes, anio


# =============================================================================
# Vista: reporte_solicitudes
# Renderiza el listado paginado (15 por página) de solicitudes resueltas,
# con filtros de estado, mes y año aplicados vía GET.
#
# Consumido por:
#   - templates/reporte/reporte.html        (tabla paginada + filtros)
#   - templates/components/navbar.html      (enlace "Reporte")
# =============================================================================
def reporte_solicitudes(request):
    solicitudes, estado, mes, anio = obtener_solicitudes_filtradas(request)

    paginator   = Paginator(solicitudes, 15)  # 15 registros por página
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    anios = range(2026, timezone.now().year + 5)  # Rango dinámico de años para el select

    context = {
        'solicitudes': page_obj,   # Página actual del paginador (iterable en reporte.html)
        'page_obj':    page_obj,   # También como page_obj para los controles de paginación
        'estado':      estado,
        'mes':         mes,
        'anio':        anio,
        'meses':       meses,
        'anios':       anios,
        'total':       paginator.count,  # Total de registros sin paginar (para el encabezado)
    }

    return render(request, 'reporte/reporte.html', context)


# =============================================================================
# Vista: reporte_solicitudes_pdf
# Genera y descarga el reporte de solicitudes como archivo PDF.
# Reutiliza obtener_solicitudes_filtradas() con los mismos filtros GET
# que reporte_solicitudes, pero sin paginar (envía todas las solicitudes).
# Usa weasyprint para renderizar reporte_pdf.html a PDF binario.
#
# Consumido por:
#   - templates/reporte/reporte.html  (botón "Descargar PDF")
# =============================================================================
def reporte_solicitudes_pdf(request):
    solicitudes, estado, mes, anio = obtener_solicitudes_filtradas(request)

    # render_to_string genera el HTML como string para pasárselo a weasyprint
    html_string = render_to_string(
        'reporte/reporte_pdf.html',
        {
            'solicitudes':     solicitudes,
            'estado':          estado,
            'mes':             mes,
            'anio':            anio,
            'total':           len(solicitudes),
            'fecha_descarga':  timezone.localtime(),  # Marca de tiempo en el encabezado del PDF
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_solicitudes.pdf"'

    # base_url permite a weasyprint resolver rutas de archivos estáticos (CSS, imágenes)
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)

    return response


# =============================================================================
# Vista: estadisticas_solicitudes
# Renderiza la página de estadísticas con métricas por estado, distribución
# mensual, top embarcaciones, distribución por tipo y crecimiento vs mes anterior.
# Soporta filtros GET de mes y año.
#
# Cálculos clave:
#   - solicitudes_mes_data: 12 entradas con total y % relativo al mes de mayor volumen
#     (% relativo al máximo, no al total, para que las barras CSS reflejen proporciones)
#   - top_embarcaciones: top 5 embarcaciones por número de solicitudes
#   - estancias_tipo_data: distribución % de solicitudes por tipo de barco
#   - crecimiento_mensual: ((mes_actual - mes_anterior) / mes_anterior) * 100
#     Si mes_anterior=0 y mes_actual>0, el crecimiento se reporta como 100%
#
# Consumido por:
#   - templates/reporte/estadisticas.html
#   - templates/components/navbar.html  (enlace "Estadísticas")
# =============================================================================
def estadisticas_solicitudes(request):
    mes  = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

    solicitudes = Solicitud.objects.select_related(
        'embarcacion',
        'embarcacion__tipo_barco'
    ).all()

    # Aplica filtros de mes y año sobre fecha_solicitud (campo de BD, no calculado)
    if mes:
        solicitudes = solicitudes.filter(fecha_solicitud__month=int(mes))
    if anio:
        solicitudes = solicitudes.filter(fecha_solicitud__year=int(anio))

    total_estadisticas = solicitudes.count()

    aprobadas  = solicitudes.filter(estado='APROBADA').count()
    rechazadas = solicitudes.filter(estado='RECHAZADA').count()
    completadas = solicitudes.filter(estado='COMPLETADA').count()
    pendientes = solicitudes.filter(estado='PENDIENTE').count()
    en_espera  = solicitudes.filter(estado='EN_ESPERA').count()
    en_proceso = pendientes + en_espera + aprobadas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas / total_estadisticas) * 100, 2)
        porcentaje_proceso     = round((en_proceso  / total_estadisticas) * 100, 2)
        porcentaje_rechazadas  = round((rechazadas  / total_estadisticas) * 100, 2)
        # tasa_aprobacion incluye tanto APROBADA como COMPLETADA (ambas son "aprobaciones exitosas")
        tasa_aprobacion = round(((aprobadas + completadas) / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = porcentaje_proceso = porcentaje_rechazadas = tasa_aprobacion = 0

    # ── Datos para gráfica de barras por mes (CSS) ───────────────────────────
    solicitudes_mes = (
        solicitudes
        .values('fecha_solicitud__month')
        .annotate(total=Count('id'))
        .order_by('fecha_solicitud__month')
    )

    meses_cortos = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    conteo_por_mes = {i: 0 for i in range(1, 13)}

    for item in solicitudes_mes:
        mes_num = item['fecha_solicitud__month']
        if mes_num:
            conteo_por_mes[mes_num] = item['total']

    maximo_mes = max(conteo_por_mes.values())  # Base para calcular porcentajes relativos

    solicitudes_mes_data = []
    for numero_mes in range(1, 13):
        total_mes = conteo_por_mes[numero_mes]
        # El % es relativo al mes de mayor volumen para que las barras CSS sean proporcionales
        porcentaje = round((total_mes / maximo_mes) * 100, 2) if maximo_mes > 0 else 0
        solicitudes_mes_data.append({
            'mes':       meses_cortos[numero_mes - 1],
            'total':     total_mes,
            'porcentaje': porcentaje,
            'activo':    total_mes > 0,  # Usado en estadisticas.html para destacar meses con datos
        })

    # ── Top 5 embarcaciones con más solicitudes ───────────────────────────────
    top_embarcaciones = (
        solicitudes
        .values('embarcacion__nombre_bote', 'embarcacion__tipo_barco__tipo_barco')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # ── Distribución % por tipo de barco ─────────────────────────────────────
    estancias_tipo = (
        solicitudes
        .values('embarcacion__tipo_barco__tipo_barco')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    total_tipo = sum(item['total'] for item in estancias_tipo)
    estancias_tipo_data = []
    for item in estancias_tipo:
        porcentaje = round((item['total'] / total_tipo) * 100, 2) if total_tipo > 0 else 0
        estancias_tipo_data.append({
            'tipo':       item['embarcacion__tipo_barco__tipo_barco'] or 'Sin tipo',
            'total':      item['total'],
            'porcentaje': porcentaje,
        })

    meses = [
        (1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),(5,'Mayo'),(6,'Junio'),
        (7,'Julio'),(8,'Agosto'),(9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre')
    ]
    anios = range(2026, timezone.now().year + 5)

    # ── Crecimiento mensual vs mes anterior ───────────────────────────────────
    mes_actual  = int(mes)  if mes  else timezone.now().month
    anio_actual = int(anio) if anio else timezone.now().year

    # Maneja el cruce de año (enero → diciembre del año anterior)
    if mes_actual == 1:
        mes_anterior  = 12
        anio_anterior = anio_actual - 1
    else:
        mes_anterior  = mes_actual - 1
        anio_anterior = anio_actual

    total_mes_actual   = Solicitud.objects.filter(
        fecha_solicitud__month=mes_actual, fecha_solicitud__year=anio_actual
    ).count()
    total_mes_anterior = Solicitud.objects.filter(
        fecha_solicitud__month=mes_anterior, fecha_solicitud__year=anio_anterior
    ).count()

    crecimiento_mensual = 0
    tipo_crecimiento    = 'neutral'

    if total_mes_anterior > 0:
        crecimiento_mensual = round(
            ((total_mes_actual - total_mes_anterior) / total_mes_anterior) * 100, 2
        )
        tipo_crecimiento = 'positivo' if crecimiento_mensual > 0 else (
            'negativo' if crecimiento_mensual < 0 else 'neutral'
        )
    elif total_mes_actual > 0:
        # Si el mes anterior no tuvo solicitudes, cualquier cantidad es +100%
        crecimiento_mensual = 100
        tipo_crecimiento    = 'positivo'

    context = {
        'mes': mes, 'anio': anio, 'meses': meses, 'anios': anios,

        'crecimiento_mensual':  crecimiento_mensual,
        'tipo_crecimiento':     tipo_crecimiento,
        'total_mes_actual':     total_mes_actual,
        'total_mes_anterior':   total_mes_anterior,

        'total_estadisticas':   total_estadisticas,
        'total_solicitudes':    total_estadisticas,  # Alias para compatibilidad en el template
        'aprobadas':            aprobadas,
        'rechazadas':           rechazadas,
        'completadas':          completadas,
        'pendientes':           pendientes,
        'en_espera':            en_espera,
        'en_proceso':           en_proceso,
        'solicitudes_aprobadas': aprobadas + completadas,  # Usadas en tasa_aprobacion del template
        'tasa_aprobacion':      tasa_aprobacion,

        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso':     porcentaje_proceso,
        'porcentaje_rechazadas':  porcentaje_rechazadas,

        'solicitudes_mes_data': solicitudes_mes_data,  # 12 entradas para las barras CSS del template
        'top_embarcaciones':    top_embarcaciones,
        'estancias_tipo_data':  estancias_tipo_data,
    }

    return render(request, 'reporte/estadisticas.html', context)


# =============================================================================
# Vista: reporte_estadisticas_pdf
# Genera y descarga las estadísticas como PDF.
# A diferencia de estadisticas_solicitudes, incluye las dos gráficas matplotlib
# (mensual y de estados) embebidas como base64 en el HTML del PDF.
# Nota: top_embarcaciones muestra top 10 aquí (vs top 5 en la vista HTML).
#
# Consumido por:
#   - templates/reporte/estadisticas.html  (botón "Descargar PDF")
# =============================================================================
def reporte_estadisticas_pdf(request):
    mes  = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')

    solicitudes = Solicitud.objects.select_related(
        'embarcacion', 'embarcacion__tipo_barco'
    ).all()

    if mes:
        solicitudes = solicitudes.filter(fecha_solicitud__month=int(mes))
    if anio:
        solicitudes = solicitudes.filter(fecha_solicitud__year=int(anio))

    total_estadisticas  = solicitudes.count()
    aprobadas_directas  = solicitudes.filter(estado='APROBADA').count()
    completadas         = solicitudes.filter(estado='COMPLETADA').count()
    rechazadas          = solicitudes.filter(estado='RECHAZADA').count()
    pendientes          = solicitudes.filter(estado='PENDIENTE').count()
    en_espera           = solicitudes.filter(estado='EN_ESPERA').count()

    # aprobadas = APROBADA + COMPLETADA (ambas son exitosas para la tasa de aprobación)
    aprobadas  = aprobadas_directas + completadas
    en_proceso = pendientes + en_espera + aprobadas_directas

    if total_estadisticas > 0:
        porcentaje_completadas = round((completadas  / total_estadisticas) * 100, 2)
        porcentaje_proceso     = round((en_proceso   / total_estadisticas) * 100, 2)
        porcentaje_rechazadas  = round((rechazadas   / total_estadisticas) * 100, 2)
        tasa_aprobacion        = round((aprobadas    / total_estadisticas) * 100, 2)
    else:
        porcentaje_completadas = porcentaje_proceso = porcentaje_rechazadas = tasa_aprobacion = 0

    # Top 10 para el PDF (más completo que el top 5 de la vista HTML)
    top_embarcaciones = (
        solicitudes
        .values('embarcacion__nombre_bote', 'embarcacion__tipo_barco__tipo_barco')
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
        porcentaje = round((item['total'] / total_tipo) * 100, 2) if total_tipo > 0 else 0
        estancias_tipo_data.append({
            'tipo':       item['embarcacion__tipo_barco__tipo_barco'] or 'Sin tipo',
            'total':      item['total'],
            'porcentaje': porcentaje,
        })

    # Genera ambas gráficas como base64 para incrustarlas en el HTML del PDF
    grafica_mensual = generar_grafica_mensual(solicitudes)
    grafica_estados = generar_grafica_estados(completadas, en_proceso, rechazadas)

    # Convierte el número de mes a nombre legible para el encabezado del PDF
    meses_dict = {
        '1':'Enero','2':'Febrero','3':'Marzo','4':'Abril',
        '5':'Mayo','6':'Junio','7':'Julio','8':'Agosto',
        '9':'Septiembre','10':'Octubre','11':'Noviembre','12':'Diciembre',
    }

    context = {
        'total_estadisticas':   total_estadisticas,
        'aprobadas':            aprobadas,
        'rechazadas':           rechazadas,
        'completadas':          completadas,
        'pendientes':           pendientes,
        'en_espera':            en_espera,
        'en_proceso':           en_proceso,
        'porcentaje_completadas': porcentaje_completadas,
        'porcentaje_proceso':     porcentaje_proceso,
        'porcentaje_rechazadas':  porcentaje_rechazadas,
        'tasa_aprobacion':        tasa_aprobacion,
        'top_embarcaciones':      top_embarcaciones,
        'estancias_tipo_data':    estancias_tipo_data,
        'grafica_mensual':        grafica_mensual,  # String base64; usado como src en <img> del PDF
        'grafica_estados':        grafica_estados,  # String base64; usado como src en <img> del PDF
        'mes':            meses_dict.get(mes, 'Todos'),
        'anio':           anio if anio else 'Todos',
        'fecha_descarga': timezone.localtime(),
    }

    html_string = render_to_string('reporte/reporte_estadisticas_pdf.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_estadisticas.pdf"'

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)

    return response