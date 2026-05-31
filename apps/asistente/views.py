# =============================================================================
# views.py — App: asistente
# Implementa el chatbot "Coral": un asistente conversacional basado en
# coincidencia de palabras clave que responde preguntas operativas sobre
# la marina (salidas, llegadas, ocupación, solicitudes pendientes, tipos
# de embarcaciones).
#
# Endpoint expuesto:
#   POST /asistente/  → view: asistente  (registrado en urls.py de esta app)
#
# Consumido por:
#   - templates/components/coral.html  (widget del chat flotante)
#   - templates/inicio.html            (incluye coral.html)
#
# Flujo de una petición:
#   coral.html (fetch POST JSON) → view asistente → detectar_intencion
#   → función de consulta BD → JsonResponse({'respuesta': '...'})
# =============================================================================

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required  # Solo usuarios autenticados pueden usar el asistente
from django.utils import timezone
from django.views.decorators.http import require_POST  # Rechaza cualquier método distinto de POST


# -----------------------------------------------------------------------------
# Vista: asistente
# Punto de entrada HTTP del chatbot. Solo acepta POST con cuerpo JSON.
# Requiere sesión autenticada (login_required).
#
# Entrada esperada (JSON):  { "mensaje": "¿cuántas embarcaciones llegan hoy?" }
# Salida (JSON):            { "respuesta": "<html con la respuesta>" }
#
# Llamado desde: templates/components/coral.html (fetch a /asistente/)
# -----------------------------------------------------------------------------
@login_required
@require_POST
def asistente(request):
    try:
        data    = json.loads(request.body)  # Parsea el cuerpo JSON de la petición
        mensaje = data.get('mensaje', '').strip().lower()  # Normaliza a minúsculas para comparación
    except Exception:
        return JsonResponse({'respuesta': 'No entendí tu pregunta. ¿Puedes reformularla?'})

    respuesta = detectar_intencion(mensaje)  # Delega la lógica al router de intenciones
    return JsonResponse({'respuesta': respuesta})


# -----------------------------------------------------------------------------
# Función: detectar_intencion
# Router de intenciones basado en coincidencia de subcadenas.
# Recibe el mensaje ya en minúsculas y retorna un string HTML con la respuesta.
# El orden de los bloques if determina la prioridad cuando un mensaje
# contiene palabras de varias categorías.
# -----------------------------------------------------------------------------
def detectar_intencion(mensaje):
    """Detecta la intención del mensaje y devuelve una respuesta."""

    # ── Salidas hoy ──────────────────────────────────────
    if any(p in mensaje for p in ['sal', 'salida', 'salen', 'se van']):
        return consulta_salidas_hoy()

    # ── Llegadas hoy ─────────────────────────────────────
    if any(p in mensaje for p in ['llega', 'llegada', 'llegan', 'arriban', 'entran']):
        return consulta_llegadas_hoy()

    # ── Solicitudes pendientes ────────────────────────────
    if any(p in mensaje for p in ['pendiente', 'esperando', 'sin asignar', 'en espera']):
        return consulta_pendientes()

    # ── Ocupación general ────────────────────────────────
    if any(p in mensaje for p in ['ocupaci', 'ocupado', 'espacio', 'disponible', 'marina']):
        return consulta_ocupacion()

    # ── Tipo de embarcación ──────────────────────────────
    # 'catamar' captura tanto 'catamaran' como 'catamarán' con una sola subcadena
    for tipo in ['velero', 'yate', 'catamar', 'lancha', 'motonave']:
        if tipo in mensaje:
            return consulta_por_tipo(tipo.upper() if tipo != 'catamar' else 'CATAMARÁN')

    # ── Saludo ────────────────────────────────────────────
    if any(p in mensaje for p in ['hola', 'buenos', 'buenas', 'hey']):
        return '¡Hola! ¿En qué puedo ayudarte hoy? 🐚'

    # ── No entendió ───────────────────────────────────────
    return (
        'No estoy seguro de cómo responder eso. '
        'Puedes preguntarme sobre <strong>salidas, llegadas, solicitudes pendientes, '
        'ocupación o tipos de embarcaciones</strong>.'
    )


# =============================================================================
# Funciones de consulta a la base de datos
# Cada función se importa de forma lazy (import dentro de la función) para
# evitar importaciones circulares en el arranque de Django.
# Todas retornan un string HTML listo para inyectar en coral.html.
# =============================================================================

# -----------------------------------------------------------------------------
# consulta_salidas_hoy
# Busca solicitudes APROBADAS cuya fecha_salida sea hoy.
# Modelos usados: apps.solicitudes.Solicitud → Embarcacion → Cliente
# -----------------------------------------------------------------------------
def consulta_salidas_hoy():
    from apps.solicitudes.models import Solicitud
    hoy = timezone.localdate()
    sols = Solicitud.objects.filter(
        estado='APROBADA',
        fecha_salida=hoy
    ).select_related('embarcacion__cliente')  # Evita N+1: trae embarcación y cliente en un JOIN

    if not sols.exists():
        return 'No hay embarcaciones programadas para salir hoy. ⚓'

    lista = ''.join(
        f'<br>• <strong>{s.embarcacion.nombre_bote}</strong> — {s.embarcacion.cliente.fullname}'
        for s in sols
    )
    return f'Hoy salen <strong>{sols.count()}</strong> embarcaciones:{lista}'


# -----------------------------------------------------------------------------
# consulta_llegadas_hoy
# Busca solicitudes APROBADAS o EN_ESPERA cuya fecha_llegada sea hoy.
# Incluye EN_ESPERA porque la embarcación puede llegar antes de ser asignada.
# Modelos usados: apps.solicitudes.Solicitud → Embarcacion → Cliente
# -----------------------------------------------------------------------------
def consulta_llegadas_hoy():
    from apps.solicitudes.models import Solicitud
    hoy = timezone.localdate()
    sols = Solicitud.objects.filter(
        estado__in=['APROBADA', 'EN_ESPERA'],
        fecha_llegada=hoy
    ).select_related('embarcacion__cliente')

    if not sols.exists():
        return 'No hay embarcaciones programadas para llegar hoy. 🌊'

    lista = ''.join(
        f'<br>• <strong>{s.embarcacion.nombre_bote}</strong> — {s.embarcacion.cliente.fullname}'
        for s in sols
    )
    return f'Hoy llegan <strong>{sols.count()}</strong> embarcaciones:{lista}'


# -----------------------------------------------------------------------------
# consulta_pendientes
# Cuenta solicitudes en estado PENDIENTE (sin revisar) y EN_ESPERA (aprobadas
# pero sin asignación de muelle). Informa el desglose al usuario.
# Modelos usados: apps.solicitudes.Solicitud
# -----------------------------------------------------------------------------
def consulta_pendientes():
    from apps.solicitudes.models import Solicitud
    pendientes  = Solicitud.objects.filter(estado='PENDIENTE').count()
    en_espera   = Solicitud.objects.filter(estado='EN_ESPERA').count()
    total = pendientes + en_espera

    if total == 0:
        return '¡Todo al día! No hay solicitudes pendientes. ✅'

    return (
        f'Hay <strong>{total}</strong> solicitudes sin resolver:<br>'
        f'• <strong>{pendientes}</strong> pendientes de revisión<br>'
        f'• <strong>{en_espera}</strong> en espera de asignación'
    )


# -----------------------------------------------------------------------------
# consulta_ocupacion
# Calcula el estado de ocupación actual de la marina:
#   - Solicitudes APROBADAS activas
#   - Espacios ocupados hoy (asignaciones activas que cubren la fecha de hoy)
#   - Espacios libres y porcentaje de ocupación
# Modelos usados: apps.solicitudes.Solicitud, apps.muelles.Espacio
# La relación Espacio → asignaciones viene del ManyToMany en Asignacion.espacios
# -----------------------------------------------------------------------------
def consulta_ocupacion():
    from apps.solicitudes.models import Solicitud
    from apps.muelles.models import Espacio
    hoy = timezone.localdate()

    aprobadas  = Solicitud.objects.filter(estado='APROBADA').count()
    # Solo espacios reales (excluye pasillos) y activos
    total_esp  = Espacio.objects.filter(es_pasillo=False, activo=True).count()
    # Espacios con al menos una asignación activa cuyo rango cubre hoy
    ocupados   = Espacio.objects.filter(
        asignaciones__activa=True,
        asignaciones__fecha_inicio__lte=hoy,
        asignaciones__fecha_fin__gte=hoy,
    ).distinct().count()  # distinct() necesario porque ManyToMany puede duplicar resultados

    libres = total_esp - ocupados
    pct    = round((ocupados / total_esp * 100), 1) if total_esp else 0

    return (
        f'Estado actual de la marina:<br>'
        f'• <strong>{aprobadas}</strong> embarcaciones actualmente asignadas<br>'
        f'• <strong>{ocupados}</strong> de {total_esp} espacios ocupados ({pct}%)<br>'
        f'• <strong>{libres}</strong> espacios disponibles'
    )


# -----------------------------------------------------------------------------
# consulta_por_tipo
# Filtra solicitudes del mes actual por tipo de embarcación (velero, yate, etc.)
# y también cuenta cuántas de ese tipo están actualmente asignadas (APROBADA).
# Modelos usados: apps.solicitudes.Solicitud → Embarcacion → TipoBarco
# El campo tipo_barco__tipo_barco usa icontains para tolerar variaciones
# de mayúsculas y caracteres especiales (ej: CATAMARÁN vs catamaran).
# -----------------------------------------------------------------------------
def consulta_por_tipo(tipo):
    from apps.solicitudes.models import Solicitud
    from django.utils import timezone
    hoy  = timezone.localdate()
    mes  = hoy.month
    anio = hoy.year

    # Solicitudes del tipo en el mes/año actual
    count = Solicitud.objects.filter(
        embarcacion__tipo_barco__tipo_barco__icontains=tipo,
        fecha_solicitud__month=mes,
        fecha_solicitud__year=anio,
    ).count()

    # De ese tipo cuántas están actualmente asignadas en la marina
    activos = Solicitud.objects.filter(
        embarcacion__tipo_barco__tipo_barco__icontains=tipo,
        estado='APROBADA',
    ).count()

    # Convierte número de mes a nombre en español para el mensaje
    nombre_mes = [
        'enero','febrero','marzo','abril','mayo','junio',
        'julio','agosto','septiembre','octubre','noviembre','diciembre'
    ][mes - 1]

    tipo_display = tipo.capitalize()
    return (
        f'Este mes (<strong>{nombre_mes}</strong>) hay '
        f'<strong>{count}</strong> solicitudes de {tipo_display}s.<br>'
        f'Actualmente <strong>{activos}</strong> {tipo_display}s están asignados en la marina.'
    )