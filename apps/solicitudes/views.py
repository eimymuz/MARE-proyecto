from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from .models import Solicitud
from django.db import models


def _auto_completar(solicitudes):
    """
    Marca como COMPLETADA las solicitudes APROBADAS cuya fecha_salida ya pasó.
    
    NOTA: En un proyecto real esto se haría con una tarea programada (cron job)
    usando Celery Beat o django-crontab, para no depender de que alguien
    abra la vista. Aquí lo hacemos al cargar la vista por simplicidad.
    """
    hoy = timezone.now().date()
    vencidas = solicitudes.filter(estado='APROBADA', fecha_salida__lt=hoy)
    for sol in vencidas:
        sol.estado = 'COMPLETADA'
        sol.save()


@login_required
def solicitud_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='PENDIENTE').order_by('-fecha_solicitud', '-id')

    # filtros de fecha — exacto si solo uno, rango si ambos
    q                  = request.GET.get('q', '').strip()
    tipo_id            = request.GET.get('tipo', '')
    primera_entrada    = request.GET.get('primera_entrada', '')

    modo_fecha    = request.GET.get('modo_fecha', 'solicitud')
    fecha_a       = request.GET.get('fecha_a', '')
    fecha_b       = request.GET.get('fecha_b', '')
    fecha_llegada = request.GET.get('fecha_llegada', '')
    fecha_salida  = request.GET.get('fecha_salida', '')

    if modo_fecha == 'solicitud':
        if fecha_a and fecha_b:
            qs = qs.filter(fecha_solicitud__range=[fecha_a, fecha_b])
        elif fecha_a:
            qs = qs.filter(fecha_solicitud=fecha_a)
        elif fecha_b:
            qs = qs.filter(fecha_solicitud=fecha_b)

    elif modo_fecha == 'llegada':
        if fecha_a and fecha_b:
            qs = qs.filter(fecha_llegada__range=[fecha_a, fecha_b])
        elif fecha_a:
            qs = qs.filter(fecha_llegada=fecha_a)
        elif fecha_b:
            qs = qs.filter(fecha_llegada=fecha_b)

    elif modo_fecha == 'salida':
        if fecha_a and fecha_b:
            qs = qs.filter(fecha_salida__range=[fecha_a, fecha_b])
        elif fecha_a:
            qs = qs.filter(fecha_salida=fecha_a)
        elif fecha_b:
            qs = qs.filter(fecha_salida=fecha_b)

    elif modo_fecha == 'estancia':
        if fecha_llegada:
            qs = qs.filter(fecha_llegada__gte=fecha_llegada)
        if fecha_salida:
            qs = qs.filter(fecha_salida__lte=fecha_salida)

    if q:
        qs = qs.filter(
            models.Q(embarcacion__nombre_bote__icontains=q) |
            models.Q(embarcacion__cliente__fullname__icontains=q)
        )
    if tipo_id:
        qs = qs.filter(embarcacion__tipo_barco_id=tipo_id)
    if primera_entrada == '1':
        qs = qs.filter(primera_entrada_mexico=True)
    
    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    from apps.embarcaciones.models import TipoBarco
    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj':    page_obj,
        'solicitudes': page_obj.object_list,
        'titulo':      'Solicitudes pendientes',
        'estado_activo': 'PENDIENTE',
        'tipos_barco': TipoBarco.objects.order_by('tipo_barco'),
        'q':              q,
        'tipo_id':        tipo_id,
        'primera_entrada': primera_entrada,
        'modo_fecha':    modo_fecha,
        'fecha_a':       fecha_a,
        'fecha_b':       fecha_b,
        'fecha_llegada': fecha_llegada,
        'fecha_salida':  fecha_salida,
        'hay_filtros': any([q, tipo_id, primera_entrada, fecha_a, fecha_b, fecha_llegada, fecha_salida]),
    })


@login_required
def solicitud_en_espera_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='EN_ESPERA').order_by('-fecha_solicitud', '-id')

    # filtros
    q           = request.GET.get('q', '').strip()
    tipo_id     = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    orden = request.GET.get('orden', 'reciente')

    if orden == 'urgente':
        qs = qs.order_by('fecha_llegada', '-id')  # llegada más próxima primero
    else:
        qs = qs.order_by('-fecha_solicitud', '-id')  # más reciente primero

    if q:
        qs = qs.filter(
            models.Q(embarcacion__nombre_bote__icontains=q) |
            models.Q(embarcacion__cliente__fullname__icontains=q)
        )
    if tipo_id:
        qs = qs.filter(embarcacion__tipo_barco_id=tipo_id)
    if fecha_desde:
        qs = qs.filter(fecha_llegada__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_llegada__lte=fecha_hasta)

    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    from apps.embarcaciones.models import TipoBarco
    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj':      page_obj,
        'solicitudes':   page_obj.object_list,
        'titulo':        'Pendientes de asignación',
        'estado_activo': 'EN_ESPERA',
        'tipos_barco':   TipoBarco.objects.order_by('tipo_barco'),
        'q':             q,
        'tipo_id':       tipo_id,
        'fecha_desde':   fecha_desde,
        'fecha_hasta':   fecha_hasta,
        'orden': orden,
        'hay_filtros':   any([q, tipo_id, fecha_desde, fecha_hasta]),
    })

@login_required
def solicitud_aprobadas_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='APROBADA')

    # auto-completar vencidas
    _auto_completar(qs)
    qs = qs.filter(estado='APROBADA')

    # filtros
    q         = request.GET.get('q', '').strip()
    muelle_id = request.GET.get('muelle', '')
    fecha_salida_desde = request.GET.get('fecha_salida_desde', '')
    fecha_salida_hasta = request.GET.get('fecha_salida_hasta', '')
    orden     = request.GET.get('orden', 'salida')
    tipo_id = request.GET.get('tipo', '')
    
    
    
    if tipo_id:
        qs = qs.filter(embarcacion__tipo_barco_id=tipo_id)

    if q:
        qs = qs.filter(
            models.Q(embarcacion__nombre_bote__icontains=q) |
            models.Q(embarcacion__cliente__fullname__icontains=q)
        )

    if muelle_id:
        qs = qs.filter(asignaciones__muelle_id=muelle_id, asignaciones__activa=True).distinct()

    if fecha_salida_desde and fecha_salida_hasta:
        qs = qs.filter(fecha_salida__range=[fecha_salida_desde, fecha_salida_hasta])
    elif fecha_salida_desde:
        qs = qs.filter(fecha_salida=fecha_salida_desde)
    elif fecha_salida_hasta:
        qs = qs.filter(fecha_salida=fecha_salida_hasta)

    # ordenamiento
    if orden == 'salida':
        qs = qs.order_by('fecha_salida', '-id')
    else:
        qs = qs.order_by('-fecha_llegada', '-id')

    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    from apps.muelles.models import Muelle
    from apps.embarcaciones.models import TipoBarco
    return render(request, 'solicitudes/solicitud_aprobadas.html', {
        'page_obj':            page_obj,
        'solicitudes':         page_obj.object_list,
        'titulo':              'Asignadas — en marina',
        'estado_activo':       'APROBADA',
        'muelles':             Muelle.objects.filter(estado=True).order_by('nombre'),
        'q':                   q,
        'muelle_id':           muelle_id,
        'fecha_salida_desde':  fecha_salida_desde,
        'fecha_salida_hasta':  fecha_salida_hasta,
        'orden':               orden,
        'tipos_barco': TipoBarco.objects.order_by('tipo_barco'),
        'tipo_id':     tipo_id,
        'hay_filtros': any([q, muelle_id, tipo_id, fecha_salida_desde, fecha_salida_hasta]),
    })



@login_required
def solicitud_update(request, pk):
    from apps.embarcaciones.models import TipoBarco
    solicitud   = get_object_or_404(
        Solicitud.objects.select_related('embarcacion__cliente','embarcacion__tipo_barco'),
        pk=pk
    )
    tipos_barco = TipoBarco.objects.order_by('tipo_barco')
    context     = {'solicitud': solicitud, 'tipos_barco': tipos_barco}

    if request.method == 'POST':
        try:
            from django.db import transaction
            with transaction.atomic():
                # actualizar cliente
                cliente          = solicitud.embarcacion.cliente
                cliente.fullname = request.POST.get('cliente_fullname','').strip()
                cliente.email    = request.POST.get('cliente_email','').strip().lower()
                cliente.telefono = request.POST.get('cliente_telefono','').strip()
                cliente.full_clean()
                cliente.save()

                # actualizar embarcación
                emb              = solicitud.embarcacion
                emb.nombre_bote  = request.POST.get('nombre_bote','').strip()
                emb.tipo_barco_id= request.POST.get('tipo_barco')
                emb.eslora       = request.POST.get('eslora')
                emb.manga        = request.POST.get('manga')
                emb.calado       = request.POST.get('calado')
                emb.full_clean()
                emb.save()

                # actualizar solicitud
                solicitud.fecha_llegada          = request.POST.get('fecha_llegada')
                solicitud.fecha_salida           = request.POST.get('fecha_salida')
                solicitud.comentario             = request.POST.get('comentario','').strip()
                solicitud.primera_entrada_mexico = request.POST.get('primera_entrada_mexico') == 'on'
                solicitud.full_clean()
                solicitud.save()

            messages.success(request, 'Solicitud actualizada correctamente.')
            destinos = {
                'PENDIENTE':  'solicitud_list',
                'EN_ESPERA':  'solicitud_en_espera_list',
                'APROBADA':   'solicitud_aprobadas_list',
                'COMPLETADA': 'solicitud_list',
                'RECHAZADA':  'solicitud_list',
            }
            return redirect(destinos.get(solicitud.estado, 'solicitud_list'))

        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc,'message_dict') else exc.messages
        except Exception as exc:
            context['errors'] = [str(exc)]

    return render(request, 'solicitudes/solicitud_form.html', context)


@login_required
def solicitud_delete(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk)
    if request.method == 'POST':
        solicitud.delete()
        messages.success(request, 'Solicitud eliminada.')
        return redirect('solicitud_list')
    return render(request, 'solicitudes/solicitud_confirm_delete.html', {
        'solicitud': solicitud
    })



@login_required
@require_POST
def solicitud_cambiar_estado(request, pk, nuevo_estado):
    solicitud       = get_object_or_404(Solicitud, pk=pk)
    estados_validos = [e[0] for e in Solicitud.ESTADOS]

    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('solicitud_list')

    # guardar motivo de rechazo si viene
    if nuevo_estado == 'RECHAZADA':
        motivo = request.POST.get('motivo_rechazo', '').strip()
        if not motivo:
            messages.error(request, 'Debes indicar el motivo de rechazo.')
            origen = request.POST.get('origen', 'list')
            if origen == 'en_espera':
                return redirect('solicitud_en_espera_list')
            elif origen == 'aprobadas':
                return redirect('solicitud_aprobadas_list')
            return redirect('solicitud_list')
        solicitud.motivo_rechazo = motivo.upper()

    solicitud.estado = nuevo_estado
    try:
        solicitud.full_clean()
        solicitud.save()
        messages.success(request, f'Estado actualizado a {solicitud.get_estado_display()}.')
    except ValidationError as exc:
        for error in (exc.messages if hasattr(exc, 'messages') else [str(exc)]):
            messages.error(request, error)

    origen = request.POST.get('origen', 'list')
    destinos = {
        'PENDIENTE':  'solicitud_list',
        'EN_ESPERA':  'solicitud_en_espera_list',
        'APROBADA':   'solicitud_aprobadas_list',
        'RECHAZADA':  'solicitud_en_espera_list' if origen == 'en_espera' else 'solicitud_aprobadas_list' if origen == 'aprobadas' else 'solicitud_list',
        'COMPLETADA': 'solicitud_aprobadas_list',
    }
    return redirect(destinos.get(nuevo_estado, 'solicitud_list'))


@login_required
def solicitud_detalle_json(request, pk):
    """API para el popup del CRUD de Asignadas."""
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'embarcacion__cliente',
            'embarcacion__tipo_barco',
        ), pk=pk
    )

    asignaciones = solicitud.asignaciones.select_related(
        'muelle', 'administrador__user'
    ).prefetch_related('espacios').order_by('-fecha_inicio')

    asignaciones_data = []
    for a in asignaciones:
        espacios = [
            {'numero': e.numero, 'muelle': e.muelle.nombre}
            for e in a.espacios.all()
        ]
        asignaciones_data.append({
            'id':           a.pk,
            'muelle':       a.muelle.nombre,
            'espacios':     espacios,
            'fecha_inicio': a.fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_fin':    a.fecha_fin.strftime('%d/%m/%Y'),
            'administrador': str(a.administrador),
        })

    return JsonResponse({
        'id':                    solicitud.pk,
        'embarcacion':           solicitud.embarcacion.nombre_bote,
        'cliente':               solicitud.embarcacion.cliente.fullname,
        'tipo':                  solicitud.embarcacion.tipo_barco.tipo_barco,
        'eslora':                float(solicitud.embarcacion.eslora),
        'manga':                 float(solicitud.embarcacion.manga),
        'calado':                float(solicitud.embarcacion.calado),
        'fecha_llegada':         solicitud.fecha_llegada.strftime('%d/%m/%Y'),
        'fecha_salida':          solicitud.fecha_salida.strftime('%d/%m/%Y'),
        'fecha_solicitud':       solicitud.fecha_solicitud.strftime('%d/%m/%Y'),
        'estado':                solicitud.get_estado_display(),
        'comentario':            solicitud.comentario or '',
        'email_cliente':         solicitud.embarcacion.cliente.email,
        'telefono_cliente':      solicitud.embarcacion.cliente.telefono,
        'primera_entrada_mexico': solicitud.primera_entrada_mexico,
        'asignaciones':          asignaciones_data,
    })