from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from apps.muelles.models import Espacio, EtiquetaMuelle, ZonaTierra
from apps.asignaciones.models import Asignacion, Administrador
from apps.solicitudes.models import Solicitud
from django.core.exceptions import ValidationError

import json
from django.db import transaction


@login_required
def mapa_view(request):
    from apps.muelles.models import Muelle
    from apps.embarcaciones.models import TipoBarco

    solicitud_id = request.GET.get('solicitud_id')
    ctx = {
        'muelles':    Muelle.objects.filter(estado=True).order_by('nombre'),
        'tipos_barco':TipoBarco.objects.order_by('tipo_barco'),
    }
    if solicitud_id:
        try:
            sol = Solicitud.objects.select_related('embarcacion__cliente').get(pk=solicitud_id)
            ctx['solicitud_ctx'] = {
                'id':            sol.pk,
                'label':         f'{sol.embarcacion.nombre_bote} — {sol.embarcacion.cliente.fullname}',
                'embarcacion':   sol.embarcacion.nombre_bote,
                'fecha_llegada': str(sol.fecha_llegada),
                'fecha_salida':  str(sol.fecha_salida),
            }
        except Solicitud.DoesNotExist:
            pass
    return render(request, 'mapa/mapa.html', ctx)


@login_required
def disponibilidad_json(request):
    fecha_str    = request.GET.get('fecha')
    solicitud_id = request.GET.get('solicitud_id')
    espacio_id   = request.GET.get('espacio_id')
    fecha        = parse_date(fecha_str) if fecha_str else None

    # Espacios ocupados en esa fecha
    ocupados = set()
    if fecha:
        asignaciones = Asignacion.objects.filter(
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
            activa=True,
        ).prefetch_related('espacios')
        for a in asignaciones:
            for e in a.espacios.all():
                ocupados.add(e.id)

    tipo_barco_id = request.GET.get('tipo_barco_id')

    # espacios ocupados por ese tipo de barco
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

    # Datos de la embarcación si viene con solicitud
    eslora = manga = None
    if solicitud_id:
        try:
            sol    = Solicitud.objects.select_related('embarcacion').get(pk=solicitud_id)
            eslora = float(sol.embarcacion.eslora)
            manga  = float(sol.embarcacion.manga)
        except Solicitud.DoesNotExist:
            pass

    # Construir respuesta de espacios
    espacios_data = []
    for e in Espacio.objects.select_related('muelle').all():
        if e.id in ocupados:
            estado = 'ocupado'
        elif eslora and manga:
            largo_m = float(e.alto)  / 10
            ancho_m = float(e.ancho) / 10
            cabe    = largo_m >= eslora and ancho_m >= manga
            if not cabe:
                estado = 'no_cabe'
            else:
                sobra_largo = largo_m - eslora
                sobra_ancho = ancho_m - manga
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
            'resaltado':  bool(tipo_barco_id) and (e.id in espacios_tipo),
        })

    zonas     = list(ZonaTierra.objects.values('id','puntos','color','nombre'))
    etiquetas = list(EtiquetaMuelle.objects.values(
        'id','muelle_id','pos_x','pos_y','texto','tamanio','color'
    ))

    # Info de asignación activa para el popup de espacio ocupado
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

    # ── GRUPOS CONTIGUOS ──────────────────────────────────────
    grupos_combinados = []
    if eslora and manga:
        from collections import defaultdict

        TOL = 8

        def se_tocan(e1, e2):
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

            if abs((x1+w1)-x2) < TOL and abs(y1-y2) < TOL: return True
            if abs((x2+w2)-x1) < TOL and abs(y1-y2) < TOL: return True
            if abs((y1+h1)-y2) < TOL and abs(x1-x2) < TOL: return True
            if abs((y2+h2)-y1) < TOL and abs(x1-x2) < TOL: return True
            return False

        def pasillo_entre(e1, e2, pasillos):
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

        por_muelle = defaultdict(list)
        for e in espacios_data:
            if not e['es_pasillo'] and e['estado'] != 'ocupado':
                por_muelle[e['muelle_id']].append(e)

        pasillos_por_muelle = defaultdict(list)
        for e in Espacio.objects.filter(es_pasillo=True).select_related('muelle'):
            pasillos_por_muelle[e.muelle_id].append({
                'pos_x': float(e.pos_x), 'pos_y': float(e.pos_y),
                'ancho': float(e.ancho), 'alto': float(e.alto),
                'rotacion': float(e.rotacion),
            })

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
        'grupos_combinados': grupos_combinados,
    })


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

    try:
        administrador = Administrador.objects.get(user=request.user)
    except Administrador.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no es administrador'}, status=403)

    try:
        solicitud = Solicitud.objects.get(pk=solicitud_id)
        espacios  = Espacio.objects.filter(id__in=espacio_ids)
        muelle    = espacios.first().muelle

        with transaction.atomic():
            traslapes = Asignacion.objects.filter(
                espacios__in=espacio_ids,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
                activa=True,
            ).exclude(solicitud=solicitud).distinct()

            if traslapes.exists():
                t = traslapes.first()
                espacio_ocupado = t.espacios.filter(id__in=espacio_ids).first()
                raise Exception(
                    f'El espacio {espacio_ocupado.numero} del muelle {espacio_ocupado.muelle.nombre} '
                    f'ya está ocupado por {t.solicitud.embarcacion.nombre_bote} '
                    f'del {t.fecha_inicio.strftime("%d/%m/%Y")} al {t.fecha_fin.strftime("%d/%m/%Y")}.'
                )

            Asignacion.objects.filter(
                solicitud=solicitud,
                activa=True
            ).update(activa=False)

            asignacion = Asignacion.objects.create(
                solicitud     = solicitud,
                muelle        = muelle,
                administrador = administrador,
                fecha_inicio  = fecha_inicio,
                fecha_fin     = fecha_fin,
                activa        = True,
            )
            asignacion.espacios.set(espacios)

            solicitud.estado = 'APROBADA'
            solicitud.full_clean()
            solicitud.save()

            return JsonResponse({'ok': True, 'asignacion_id': asignacion.pk})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
def inicio(request):
    hoy = timezone.now().date()

    ocupados = Asignacion.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
        activa=True,
    ).values_list('espacios', flat=True).distinct().count()

    total_espacios = Espacio.objects.filter(es_pasillo=False, activo=True).count()
    libres         = total_espacios - ocupados
    pendientes     = Solicitud.objects.filter(estado__in=['PENDIENTE','EN_ESPERA']).count()

    return render(request, 'inicio.html', {
        'ocupados':       ocupados,
        'libres':         libres,
        'pendientes':     pendientes,
        'total_espacios': total_espacios,
        'fecha_hoy':      hoy.strftime('%d/%m/%Y'),
        'fecha_hoy_iso':  hoy.strftime('%Y-%m-%d'),
    })