# apps/asistente/views.py
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST


@login_required
@require_POST
def asistente(request):
    try:
        data    = json.loads(request.body)
        mensaje = data.get('mensaje', '').strip().lower()
    except Exception:
        return JsonResponse({'respuesta': 'No entendí tu pregunta. ¿Puedes reformularla?'})

    respuesta = detectar_intencion(mensaje)
    return JsonResponse({'respuesta': respuesta})


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


# ── Consultas a la BD ─────────────────────────────────────

def consulta_salidas_hoy():
    from apps.solicitudes.models import Solicitud
    hoy = timezone.localdate()
    sols = Solicitud.objects.filter(
        estado='APROBADA',
        fecha_salida=hoy
    ).select_related('embarcacion__cliente')

    if not sols.exists():
        return 'No hay embarcaciones programadas para salir hoy. ⚓'

    lista = ''.join(
        f'<br>• <strong>{s.embarcacion.nombre_bote}</strong> — {s.embarcacion.cliente.fullname}'
        for s in sols
    )
    return f'Hoy salen <strong>{sols.count()}</strong> embarcaciones:{lista}'


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


def consulta_ocupacion():
    from apps.solicitudes.models import Solicitud
    from apps.muelles.models import Espacio
    hoy = timezone.localdate()

    aprobadas  = Solicitud.objects.filter(estado='APROBADA').count()
    total_esp  = Espacio.objects.filter(es_pasillo=False, activo=True).count()
    ocupados   = Espacio.objects.filter(
        asignaciones__activa=True,
        asignaciones__fecha_inicio__lte=hoy,
        asignaciones__fecha_fin__gte=hoy,
    ).distinct().count()

    libres = total_esp - ocupados
    pct    = round((ocupados / total_esp * 100), 1) if total_esp else 0

    return (
        f'Estado actual de la marina:<br>'
        f'• <strong>{aprobadas}</strong> embarcaciones actualmente asignadas<br>'
        f'• <strong>{ocupados}</strong> de {total_esp} espacios ocupados ({pct}%)<br>'
        f'• <strong>{libres}</strong> espacios disponibles'
    )


def consulta_por_tipo(tipo):
    from apps.solicitudes.models import Solicitud
    from django.utils import timezone
    hoy  = timezone.localdate()
    mes  = hoy.month
    anio = hoy.year

    count = Solicitud.objects.filter(
        embarcacion__tipo_barco__tipo_barco__icontains=tipo,
        fecha_solicitud__month=mes,
        fecha_solicitud__year=anio,
    ).count()

    activos = Solicitud.objects.filter(
        embarcacion__tipo_barco__tipo_barco__icontains=tipo,
        estado='APROBADA',
    ).count()

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