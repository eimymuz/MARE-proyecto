from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from apps.muelles.models import Espacio, EtiquetaMuelle, ZonaTierra
from apps.asignaciones.models import Asignacion, Administrador
from apps.solicitudes.models import Solicitud

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
            'resaltado': bool(tipo_barco_id) and (e.id in espacios_tipo),
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

    return JsonResponse({
        'espacios':         espacios_data,
        'zonas':            zonas,
        'etiquetas':        etiquetas,
        'fecha':            fecha_str,
        'eslora':           eslora,
        'manga':            manga,
        'asignacion_activa':asignacion_activa,
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
            asignacion.validar_traslape_espacios()

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