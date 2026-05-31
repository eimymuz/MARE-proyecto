# =============================================================================
# views.py — App: mapa
# Contiene las tres vistas principales del sistema: el mapa interactivo de la
# marina, su API de disponibilidad de espacios, la acción de asignar espacio,
# y el dashboard de inicio.
#
# Vistas:
#   mapa_view          GET  /mapa/             → template: mapa/mapa.html
#   disponibilidad_json GET  /mapa/disponibilidad/ → JsonResponse (consumido por mapa_component.html y mapa.html vía JS)
#   asignar_espacio    POST /mapa/asignar/     → JsonResponse (consumido por mapa_component.html vía JS)
#   inicio             GET  /                  → template: inicio.html
#
# Modelos usados:
#   apps.muelles:      Espacio, EtiquetaMuelle, ZonaTierra, Muelle
#   apps.asignaciones: Asignacion, Administrador
#   apps.solicitudes:  Solicitud, SolicitudHistorial
#   apps.embarcaciones: TipoBarco (import lazy en mapa_view)
#   apps.mapa.services: obtener_clima (API externa Open-Meteo)
# =============================================================================

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date           # Convierte string 'YYYY-MM-DD' a objeto date
from django.utils import timezone
from apps.muelles.models import Espacio, EtiquetaMuelle, ZonaTierra
from apps.asignaciones.models import Asignacion, Administrador
from apps.mapa.services.marine_api import obtener_clima  # Servicio de clima externo (Open-Meteo)
from apps.solicitudes.models import Solicitud
from django.core.exceptions import ValidationError
from apps.solicitudes.models import Solicitud, SolicitudHistorial  # SolicitudHistorial para auditoría de cambios de estado

import json
from django.db import transaction  # Garantiza atomicidad al crear asignaciones


# =============================================================================
# Vista: mapa_view
# Renderiza la página del mapa interactivo de la marina.
# Si recibe ?solicitud_id=N en la URL, precarga los datos de esa solicitud
# en el contexto para que mapa.html los inyecte en el JS del mapa
# (permite ir directo desde solicitud_list.html al mapa con la solicitud activa).
#
# Consumido por:
#   - templates/mapa/mapa.html          (template principal del mapa)
#   - templates/solicitudes/solicitud_list.html  (botón "Asignar" → ?solicitud_id=N)
#   - templates/solicitudes/solicitud_aprobadas.html (botón "Reasignar")
# =============================================================================
@login_required
def mapa_view(request):
    from apps.muelles.models import Muelle          # Import lazy para evitar posibles circulares al arrancar
    from apps.embarcaciones.models import TipoBarco # Import lazy; se usa solo en esta vista

    solicitud_id = request.GET.get('solicitud_id')  # Opcional: viene desde solicitud_list o solicitud_aprobadas
    ctx = {
        # Solo muelles activos; se usan en el filtro lateral del mapa
        'muelles':     Muelle.objects.filter(estado=True).order_by('nombre'),
        # Tipos de barco para el filtro de resaltado por tipo en el mapa
        'tipos_barco': TipoBarco.objects.order_by('tipo_barco'),
    }
    if solicitud_id:
        try:
            sol = Solicitud.objects.select_related('embarcacion__cliente').get(pk=solicitud_id)
            # solicitud_ctx es leído por mapa.html para precargar la solicitud en el JS
            ctx['solicitud_ctx'] = {
                'id':            sol.pk,
                'label':         f'{sol.embarcacion.nombre_bote} — {sol.embarcacion.cliente.fullname}',
                'embarcacion':   sol.embarcacion.nombre_bote,
                'fecha_llegada': str(sol.fecha_llegada),
                'fecha_salida':  str(sol.fecha_salida),
            }
        except Solicitud.DoesNotExist:
            pass
    # from_mapa=True indica a mapa.html que el acceso fue directo (no desde solicitud_list),
    # usado para ajustar el comportamiento del botón "Volver" en el template
    ctx['from_mapa'] = request.GET.get('from') == 'mapa'
    return render(request, 'mapa/mapa.html', ctx)


# =============================================================================
# Vista: disponibilidad_json
# API GET que devuelve el estado actual de todos los espacios de la marina
# para una fecha dada, con coloreado según disponibilidad y ajuste a las
# dimensiones de la embarcación a asignar.
#
# Parámetros GET:
#   fecha        (str YYYY-MM-DD): fecha para la que se consulta disponibilidad
#   solicitud_id (int, opcional):  si viene, obtiene eslora/manga de la embarcación
#   espacio_id   (int, opcional):  si viene, devuelve info de la asignación activa en ese espacio
#   tipo_barco_id (int, opcional): resalta espacios ocupados por ese tipo de barco
#
# Respuesta JSON:
#   espacios[]          → lista con estado de cada espacio (libre/ocupado/ideal/posible/no_cabe)
#   zonas[]             → polígonos de ZonaTierra para el canvas del mapa
#   etiquetas[]         → EtiquetaMuelle para labels sobre el mapa
#   asignacion_activa   → datos del inquilino actual de espacio_id (si aplica)
#   grupos_combinados[] → pares de espacios contiguos que juntos admiten la embarcación
#
# Consumido por:
#   - templates/mapa/mapa_component.html  (fetch GET en JS para redibujar el mapa)
#   - templates/mapa/mapa.html            (misma lógica vía mapa_component)
# =============================================================================
@login_required
def disponibilidad_json(request):
    fecha_str    = request.GET.get('fecha')
    solicitud_id = request.GET.get('solicitud_id')
    espacio_id   = request.GET.get('espacio_id')
    fecha        = parse_date(fecha_str) if fecha_str else None

    # ── Espacios ocupados en esa fecha ───────────────────────────────────────
    # Recorre asignaciones activas que cubren la fecha y acumula IDs de espacios
    ocupados = set()
    if fecha:
        asignaciones = Asignacion.objects.filter(
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
            activa=True,
        ).prefetch_related('espacios')  # prefetch evita N+1 al iterar a.espacios.all()
        for a in asignaciones:
            for e in a.espacios.all():
                ocupados.add(e.id)

    tipo_barco_id = request.GET.get('tipo_barco_id')

    # ── Espacios ocupados por ese tipo de barco (para resaltado) ─────────────
    # Permite al usuario ver visualmente qué espacios usa habitualmente ese tipo
    espacios_tipo = set()
    if tipo_barco_id and fecha:
        asigs_tipo = Asignacion.objects.filter(
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
            activa=True,
            solicitud__embarcacion__tipo_barco_id=tipo_barco_id,
        ).prefetch_related('espacios')
        for a in asigs_tipo:
            for e in a.espacios.all():
                espacios_tipo.add(e.id)

    # ── Dimensiones de la embarcación para cálculo de ajuste ─────────────────
    # Si viene solicitud_id, obtiene eslora y manga para clasificar cada espacio
    eslora = manga = None
    if solicitud_id:
        try:
            sol    = Solicitud.objects.select_related('embarcacion').get(pk=solicitud_id)
            eslora = float(sol.embarcacion.eslora)
            manga  = float(sol.embarcacion.manga)
        except Solicitud.DoesNotExist:
            pass

    # ── Construir lista de espacios con su estado ────────────────────────────
    # Las coordenadas (pos_x, pos_y, ancho, alto) están en píxeles del canvas;
    # se dividen /10 para convertir a metros y comparar con eslora/manga.
    # Estados posibles:
    #   'ocupado'  → ya tiene asignación activa en esa fecha
    #   'no_cabe'  → las dimensiones del espacio no admiten la embarcación
    #   'ideal'    → cabe y el espacio sobrante es ≤ 30% (buen ajuste)
    #   'posible'  → cabe pero queda mucho espacio libre (>30%)
    #   'libre'    → no hay solicitud para comparar; sin asignación activa
    espacios_data = []
    for e in Espacio.objects.select_related('muelle').all():
        if e.id in ocupados:
            estado = 'ocupado'
        elif eslora and manga:
            largo_m = float(e.alto)  / 10  # alto del canvas → largo real en metros
            ancho_m = float(e.ancho) / 10  # ancho del canvas → ancho real en metros
            cabe    = largo_m >= eslora and ancho_m >= manga
            if not cabe:
                estado = 'no_cabe'
            else:
                sobra_largo = largo_m - eslora
                sobra_ancho = ancho_m - manga
                # Porcentaje de área sobrante respecto al área total del espacio
                pct = ((sobra_largo * sobra_ancho) / (largo_m * ancho_m)) * 100
                estado = 'ideal' if pct <= 30 else 'posible'
        else:
            estado = 'libre'

        espacios_data.append({
            'id':         e.id,
            'numero':     e.numero,
            'muelle_id':  e.muelle_id,
            'muelle':     e.muelle.nombre,
            'pos_x':      float(e.pos_x),
            'pos_y':      float(e.pos_y),
            'ancho':      float(e.ancho),
            'alto':       float(e.alto),
            'rotacion':   float(e.rotacion),
            'es_pasillo': e.es_pasillo,
            'estado':     estado,
            # resaltado=True si el tipo_barco_id está ocupando ese espacio (visual de referencia)
            'resaltado':  bool(tipo_barco_id) and (e.id in espacios_tipo),
        })

    # Zonas de tierra y etiquetas de muelles para el canvas del mapa
    zonas     = list(ZonaTierra.objects.values('id','puntos','color','nombre'))
    etiquetas = list(EtiquetaMuelle.objects.values(
        'id','muelle_id','pos_x','pos_y','texto','tamanio','color'
    ))

    # ── Info de asignación activa para popup de espacio ocupado ──────────────
    # Si el usuario hace clic en un espacio ocupado, el JS pide este endpoint
    # con espacio_id para mostrar los datos del ocupante actual en un popup
    asignacion_activa = None
    if espacio_id and fecha:
        try:
            a = Asignacion.objects.select_related(
                'solicitud__embarcacion__cliente'
            ).get(
                espacios__id=espacio_id,
                fecha_inicio__lte=fecha,
                fecha_fin__gte=fecha,
                activa=True,
            )
            asignacion_activa = {
                'solicitud_id': a.solicitud_id,
                'embarcacion':  a.solicitud.embarcacion.nombre_bote,
                'cliente':      a.solicitud.embarcacion.cliente.fullname,
                'fecha_inicio': a.fecha_inicio.strftime('%d/%m/%Y'),
                'fecha_fin':    a.fecha_fin.strftime('%d/%m/%Y'),
            }
        except Asignacion.DoesNotExist:
            pass

    # ── GRUPOS CONTIGUOS ─────────────────────────────────────────────────────
    # Cuando la embarcación no cabe en un solo espacio, detecta pares de espacios
    # adyacentes que juntos sí la admiten. Solo se calcula si se conocen eslora y manga.
    grupos_combinados = []
    if eslora and manga:
        from collections import defaultdict

        TOL = 8  # Tolerancia en píxeles para considerar dos espacios como contiguos

        def se_tocan(e1, e2):
            """Determina si dos espacios comparten un borde (dentro de TOL píxeles).
            Tiene en cuenta la rotación para intercambiar ancho/alto cuando
            el espacio está rotado 90° o 270°."""
            rot1 = e1.get('rotacion', 0)
            if rot1 in (90, 270):
                w1 = float(e1['alto'])
                h1 = float(e1['ancho'])
            else:
                w1 = float(e1['ancho'])
                h1 = float(e1['alto'])

            rot2 = e2.get('rotacion', 0)
            if rot2 in (90, 270):
                w2 = float(e2['alto'])
                h2 = float(e2['ancho'])
            else:
                w2 = float(e2['ancho'])
                h2 = float(e2['alto'])

            x1, y1 = float(e1['pos_x']), float(e1['pos_y'])
            x2, y2 = float(e2['pos_x']), float(e2['pos_y'])

            # Verifica los cuatro posibles bordes compartidos (derecha, izquierda, abajo, arriba)
            if abs((x1+w1)-x2) < TOL and abs(y1-y2) < TOL: return True
            if abs((x2+w2)-x1) < TOL and abs(y1-y2) < TOL: return True
            if abs((y1+h1)-y2) < TOL and abs(x1-x2) < TOL: return True
            if abs((y2+h2)-y1) < TOL and abs(x1-x2) < TOL: return True
            return False

        def pasillo_entre(e1, e2, pasillos):
            """Verifica si hay un pasillo entre dos espacios contiguos.
            Si hay un pasillo en el área delimitada por ambos espacios, no se
            pueden combinar (el pasillo separa físicamente los amarres)."""
            mx1 = min(e1['pos_x'], e2['pos_x'])
            mx2 = max(e1['pos_x'] + e1['ancho'], e2['pos_x'] + e2['ancho'])
            my1 = min(e1['pos_y'], e2['pos_y'])
            my2 = max(e1['pos_y'] + e1['alto'], e2['pos_y'] + e2['alto'])
            for p in pasillos:
                px1, px2 = p['pos_x'], p['pos_x'] + p['ancho']
                py1, py2 = p['pos_y'], p['pos_y'] + p['alto']
                if px1 > mx1 - TOL and px2 < mx2 + TOL and py1 > my1 - TOL and py2 < my2 + TOL:
                    return True
            return False

        def calcular_dimensiones_grupo(e1, e2, direccion):
            """Calcula las dimensiones combinadas de dos espacios contiguos.
            La dimensión que crece depende de la dirección de unión y la rotación:
            - Sin rotación + vertical  → los altos se suman (eslora crece)
            - Sin rotación + horizontal → los anchos se suman (manga crece)
            - Con rotación 90/270, los ejes se invierten."""
            alto1  = float(e1['alto'])
            ancho1 = float(e1['ancho'])
            alto2  = float(e2['alto'])
            ancho2 = float(e2['ancho'])
            rot = e1.get('rotacion', 0)

            if rot == 0:
                if direccion == 'vertical':
                    # uno encima del otro → eslora crece
                    return (alto1 + alto2) / 10, max(ancho1, ancho2) / 10
                else:
                    # lado a lado → manga crece
                    return max(alto1, alto2) / 10, (ancho1 + ancho2) / 10
            else:  # rot=90 o 270
                if direccion == 'vertical':
                    # lado a lado → manga crece
                    return max(alto1, alto2) / 10, (ancho1 + ancho2) / 10
                else:
                    # uno detrás del otro → eslora crece
                    return (alto1 + alto2) / 10, max(ancho1, ancho2) / 10

        def detectar_dir(e1, e2):
            """Detecta si dos espacios se unen en dirección horizontal o vertical
            comparando sus posiciones X e Y con la anchura efectiva (considerando rotación)."""
            rot1 = e1.get('rotacion', 0)
            if rot1 in (90, 270):
                w1 = float(e1['alto']); h1 = float(e1['ancho'])
            else:
                w1 = float(e1['ancho']); h1 = float(e1['alto'])
            x1,y1 = float(e1['pos_x']),float(e1['pos_y'])
            x2,y2 = float(e2['pos_x']),float(e2['pos_y'])
            rot2 = e2.get('rotacion', 0)
            if rot2 in (90, 270):
                w2 = float(e2['alto'])
            else:
                w2 = float(e2['ancho'])
            if abs((x1+w1)-x2)<TOL or abs((x2+w2)-x1)<TOL: return 'horizontal'
            return 'vertical'

        # Agrupa espacios disponibles (no pasillo, no ocupado) por muelle
        por_muelle = defaultdict(list)
        for e in espacios_data:
            if not e['es_pasillo'] and e['estado'] != 'ocupado':
                por_muelle[e['muelle_id']].append(e)

        # Carga pasillos por muelle para usar en pasillo_entre()
        pasillos_por_muelle = defaultdict(list)
        for e in Espacio.objects.filter(es_pasillo=True).select_related('muelle'):
            pasillos_por_muelle[e.muelle_id].append({
                'pos_x': float(e.pos_x), 'pos_y': float(e.pos_y),
                'ancho': float(e.ancho), 'alto': float(e.alto),
                'rotacion': float(e.rotacion),
            })

        # Revisión de todos los pares de espacios dentro de cada muelle
        for muelle_id, espacios_muelle in por_muelle.items():
            pasillos = pasillos_por_muelle[muelle_id]
            n = len(espacios_muelle)
            for i in range(n):
                for j in range(i+1, n):
                    e1, e2 = espacios_muelle[i], espacios_muelle[j]
                    if se_tocan(e1, e2) and not pasillo_entre(e1, e2, pasillos):
                        direccion = detectar_dir(e1, e2)
                        eslora_g, manga_g = calcular_dimensiones_grupo(e1, e2, direccion)
                        if eslora_g >= eslora and manga_g >= manga:
                            sobra = ((eslora_g - eslora) * (manga_g - manga)) / (eslora_g * manga_g) * 100
                            estado_g = 'ideal' if sobra <= 30 else 'posible'
                            grupos_combinados.append({
                                'ids':    [e1['id'], e2['id']],
                                'estado': estado_g,
                            })

    return JsonResponse({
        'espacios':          espacios_data,
        'zonas':             zonas,
        'etiquetas':         etiquetas,
        'fecha':             fecha_str,
        'eslora':            eslora,
        'manga':             manga,
        'asignacion_activa': asignacion_activa,
        'grupos_combinados': grupos_combinados,  # Leído por mapa_component.html para resaltar pares combinables
    })


# =============================================================================
# Vista: asignar_espacio
# Acción POST que registra formalmente la asignación de uno o más espacios
# a una solicitud. Es la operación central del flujo de asignación.
#
# Flujo completo:
#   1. Parsea JSON del body (solicitud_id, espacio_ids, fecha_inicio, fecha_fin)
#   2. Verifica que el usuario tenga perfil de Administrador
#   3. Verifica que no sea una asignación nueva con fecha ya vencida
#   4. Dentro de transaction.atomic():
#      a. Detecta traslapes con otras asignaciones activas → error 400 con detalle
#      b. Desactiva asignaciones previas de la misma solicitud (reasignación)
#      c. Crea la nueva Asignacion y asigna los espacios (ManyToMany .set())
#      d. Cambia el estado de la Solicitud a APROBADA y registra en SolicitudHistorial
#
# Consumido por:
#   - templates/mapa/mapa_component.html  (fetch POST desde el JS del mapa)
# =============================================================================
@login_required
def asignar_espacio(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    try:
        data         = json.loads(request.body)
        solicitud_id = int(data['solicitud_id'])
        espacio_ids  = data['espacio_ids']
        fecha_inicio = parse_date(data['fecha_inicio'])
        fecha_fin    = parse_date(data['fecha_fin'])
    except (KeyError, ValueError, TypeError) as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    # Solo administradores registrados pueden asignar
    try:
        administrador = Administrador.objects.get(user=request.user)
    except Administrador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no es administrador'}, status=403)

    try:
        from django.utils.timezone import localdate
        from apps.solicitudes.models import SolicitudHistorial

        solicitud = Solicitud.objects.get(pk=solicitud_id)
        espacios  = Espacio.objects.filter(id__in=espacio_ids)
        muelle    = espacios.first().muelle  # Todos los espacios seleccionados deben ser del mismo muelle

        # Validar que la solicitud no sea reasignación con fecha ya vencida
        # es_reasignacion=True → ya tiene asignación activa → es un cambio de espacio, se permite
        es_reasignacion = Asignacion.objects.filter(solicitud=solicitud, activa=True).exists()
        if not es_reasignacion and fecha_inicio < localdate():
            return JsonResponse({
                'ok': False,
                'error': 'La fecha de llegada ya pasó. No se puede asignar este espacio.'
            }, status=400)

        with transaction.atomic():
            # Busca traslapes: otros espacios de la misma lista que ya están asignados en esas fechas
            # Se excluye la propia solicitud para permitir reasignación al mismo espacio
            traslapes = Asignacion.objects.filter(
                espacios__in=espacio_ids,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
                activa=True,
            ).exclude(solicitud=solicitud).distinct()

            if traslapes.exists():
                # Devuelve detalles del conflicto para mostrarlos en el popup de error del mapa
                t = traslapes.first()
                espacio_ocupado = t.espacios.filter(id__in=espacio_ids).first()
                emb = t.solicitud.embarcacion
                return JsonResponse({
                    'ok': False,
                    'error_tipo': 'ocupado',
                    'espacio':    f'{espacio_ocupado.muelle.nombre}-{espacio_ocupado.numero}',
                    'embarcacion': emb.nombre_bote,
                    'cliente':     emb.cliente.fullname,
                    'tipo':        emb.tipo_barco.tipo_barco,
                    'eslora':      float(emb.eslora),
                    'manga':       float(emb.manga),
                    'calado':      float(emb.calado),
                    'fecha_inicio': t.fecha_inicio.strftime('%d/%m/%Y'),
                    'fecha_fin':    t.fecha_fin.strftime('%d/%m/%Y'),
                }, status=400)

            # Desactiva asignaciones anteriores de esta solicitud (reasignación = soft-delete)
            Asignacion.objects.filter(
                solicitud=solicitud,
                activa=True
            ).update(activa=False)

            # Crea la nueva asignación y asigna los espacios vía ManyToMany
            asignacion = Asignacion.objects.create(
                solicitud     = solicitud,
                muelle        = muelle,
                administrador = administrador,
                fecha_inicio  = fecha_inicio,
                fecha_fin     = fecha_fin,
                activa        = True,
            )
            asignacion.espacios.set(espacios)  # Reemplaza los espacios M2M de una sola vez

            # Usa .update() en lugar de .save() para evitar pasar por clean() de Solicitud,
            # que podría rechazar el cambio de estado si hay validaciones de campos no cargados
            if solicitud.estado != 'APROBADA':
                estado_anterior = solicitud.estado
                Solicitud.objects.filter(pk=solicitud.pk).update(estado='APROBADA')
                # Registra el cambio en el historial de auditoría de la solicitud
                SolicitudHistorial.objects.create(
                    solicitud=solicitud,
                    estado_anterior=estado_anterior,
                    estado_nuevo='APROBADA',
                )

            return JsonResponse({'ok': True, 'asignacion_id': asignacion.pk})

    except ValidationError as e:
        msgs = list(e.messages) if hasattr(e, 'messages') else [str(e)]
        return JsonResponse({'ok': False, 'error': msgs[0]}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# =============================================================================
# Vista: inicio
# Renderiza el dashboard principal del sistema (inicio.html).
# Recopila métricas de ocupación en tiempo real, actividad del día y clima.
#
# Datos enviados al template inicio.html:
#   ocupados              → cantidad de espacios con asignación activa hoy
#   libres                → espacios activos sin asignación activa hoy
#   total_espacios        → total de espacios activos (sin pasillos)
#   porcentaje_ocupacion  → (ocupados / total) * 100, redondeado
#   pendientes            → solicitudes en estado PENDIENTE o EN_ESPERA
#   llegadas_hoy          → conteo de solicitudes APROBADAS con fecha_llegada=hoy
#   salidas_hoy           → conteo de solicitudes APROBADAS con fecha_salida=hoy
#   llegadas_embarcaciones → queryset con detalle para el popup de llegadas
#   salidas_embarcaciones  → queryset con detalle para el popup de salidas
#   asignaciones_activas   → queryset con asignaciones activas hoy para popup de ocupación
#   clima                  → dict con temperatura, viento, descripción e icono (Open-Meteo)
#   fecha_hoy / fecha_hoy_iso → fecha formateada para display y para inputs de fecha en JS
#
# Consumido por:
#   - templates/inicio.html  (dashboard principal)
# =============================================================================
@login_required
def inicio(request):
    hoy = timezone.now().date()

    # Espacios ocupados hoy: asignaciones activas cuyo rango cubre hoy
    # values_list + distinct evita contar duplicados si un espacio tiene varias asignaciones
    ocupados = Asignacion.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
        activa=True,
    ).values_list('espacios', flat=True).distinct().count()

    # Solo espacios reales (excluye pasillos) y activos para el denominador de ocupación
    total_espacios = Espacio.objects.filter(
        es_pasillo=False,
        activo=True
    ).count()

    libres = total_espacios - ocupados

    # Solicitudes que necesitan atención: aún sin asignar (PENDIENTE) o esperando espacio (EN_ESPERA)
    pendientes = Solicitud.objects.filter(
        estado__in=['PENDIENTE', 'EN_ESPERA']
    ).count()

    # LLEGADAS HOY
    llegadas_hoy = Solicitud.objects.filter(
        fecha_llegada=hoy,
        estado='APROBADA'
    ).count()

    # SALIDAS HOY
    salidas_hoy = Solicitud.objects.filter(
        fecha_salida=hoy,
        estado='APROBADA'
    ).count()

    # LLEGADAS EMBARCACIONES (para popup)
    # select_related evita N+1 al renderizar nombre_bote, fullname, tipo_barco en inicio.html
    llegadas_embarcaciones = Solicitud.objects.filter(
        fecha_llegada=hoy,
        estado='APROBADA'
    ).select_related('embarcacion__cliente', 'embarcacion__tipo_barco')

    # SALIDAS EMBARCACIONES (para popup)
    salidas_embarcaciones = Solicitud.objects.filter(
        fecha_salida=hoy,
        estado='APROBADA'
    ).select_related('embarcacion__cliente', 'embarcacion__tipo_barco')

    # ASIGNACIONES ACTIVAS (para popup de ocupación en inicio.html)
    asignaciones_activas = Asignacion.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
        activa=True
    ).select_related('solicitud__embarcacion__cliente', 'muelle')

    if total_espacios > 0:
        porcentaje_ocupacion = round((ocupados / total_espacios) * 100)
    else:
        porcentaje_ocupacion = 0

    # Llama a la API de clima externa (Open-Meteo); si falla retorna valores "--"
    clima = obtener_clima()

    return render(request, 'inicio.html', {
        'ocupados': ocupados,
        'libres': libres,
        'pendientes': pendientes,
        'total_espacios': total_espacios,
        'porcentaje_ocupacion': porcentaje_ocupacion,
        'clima': clima,

        # NUEVOS DATOS
        'llegadas_hoy': llegadas_hoy,
        'salidas_hoy': salidas_hoy,
        'llegadas_embarcaciones': llegadas_embarcaciones,
        'salidas_embarcaciones': salidas_embarcaciones,
        'asignaciones_activas': asignaciones_activas,

        'fecha_hoy':     hoy.strftime('%d/%m/%Y'),   # Para mostrar en el dashboard
        'fecha_hoy_iso': hoy.strftime('%Y-%m-%d'),   # Para inputs type="date" y fetch JS
    })