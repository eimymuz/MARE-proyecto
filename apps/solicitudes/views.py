# =============================================================================
# views.py — App: solicitudes
# Gestión completa del ciclo de vida de las solicitudes de ingreso a la marina.
#
# Vistas:
#   solicitud_list            GET  /solicitudes/               → solicitudes/solicitud_list.html
#   solicitud_en_espera_list  GET  /solicitudes/en-espera/     → solicitudes/solicitud_list.html
#   solicitud_aprobadas_list  GET  /solicitudes/aprobadas/     → solicitudes/solicitud_aprobadas.html
#   solicitud_update          GET/POST /solicitudes/<pk>/editar/ → solicitudes/solicitud_form.html
#   solicitud_cambiar_estado  POST /solicitudes/<pk>/estado/<nuevo_estado>/ → redirect
#   solicitud_detalle_json    GET  /solicitudes/<pk>/json/     → JsonResponse
#
# Función auxiliar:
#   _auto_completar → marca COMPLETADAS las solicitudes APROBADAS con fecha_salida vencida
#
# Modelos usados:
#   Solicitud, apps.embarcaciones.TipoBarco, apps.muelles.Muelle,
#   apps.asignaciones.Asignacion (import lazy en solicitud_cambiar_estado)
# =============================================================================

from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST  # solicitud_cambiar_estado solo acepta POST
from django.utils import timezone
from django.http import JsonResponse
from .models import Solicitud
from django.db import models  # Usado para models.Q en los filtros de búsqueda


# =============================================================================
# _auto_completar
# Función auxiliar que transita a COMPLETADA las solicitudes APROBADAS cuya
# fecha_salida ya pasó. Se ejecuta al inicio de solicitud_aprobadas_list.
#
# NOTA: En producción esto debería hacerse con una tarea programada (cron job)
# usando Celery Beat o django-crontab para no depender de que alguien abra la
# vista. Aquí se hace en la carga de la vista por simplicidad de despliegue.
#
# Llama a sol.save() en cada vencida para que Solicitud.save() registre el
# cambio automáticamente en SolicitudHistorial.
# =============================================================================
def _auto_completar(solicitudes):
    hoy      = timezone.now().date()
    vencidas = solicitudes.filter(estado='APROBADA', fecha_salida__lt=hoy)
    for sol in vencidas:
        sol.estado = 'COMPLETADA'
        sol.save()  # Dispara SolicitudHistorial via Solicitud.save()


# =============================================================================
# Vista: solicitud_list
# Lista paginada (10/pág) de solicitudes en estado PENDIENTE.
# Soporta filtros GET combinables: búsqueda de texto (q), tipo de barco,
# primera entrada a México y filtros de fecha en cuatro modos:
#   'solicitud' → filtra por fecha_solicitud
#   'llegada'   → filtra por fecha_llegada
#   'salida'    → filtra por fecha_salida
#   'estancia'  → filtra por rango fecha_llegada ≥ X y fecha_salida ≤ Y
# Si se dan fecha_a y fecha_b → __range; si solo uno → exacto.
#
# hay_filtros: bool para que solicitud_list.html muestre el botón "Limpiar filtros"
#
# Consumido por:
#   - templates/solicitudes/solicitud_list.html  (estado_activo='PENDIENTE')
#   - templates/components/navbar.html            (enlace "Solicitudes")
# =============================================================================
@login_required
def solicitud_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='PENDIENTE').order_by('-fecha_solicitud', '-id')

    q               = request.GET.get('q', '').strip()
    tipo_id         = request.GET.get('tipo', '')
    primera_entrada = request.GET.get('primera_entrada', '')
    modo_fecha      = request.GET.get('modo_fecha', 'solicitud')
    fecha_a         = request.GET.get('fecha_a', '')
    fecha_b         = request.GET.get('fecha_b', '')
    fecha_llegada   = request.GET.get('fecha_llegada', '')
    fecha_salida    = request.GET.get('fecha_salida', '')

    # Aplica el filtro de fecha según el modo seleccionado en el template
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
        # Busca solicitudes cuya estancia se solapa con el rango indicado
        if fecha_llegada:
            qs = qs.filter(fecha_llegada__gte=fecha_llegada)
        if fecha_salida:
            qs = qs.filter(fecha_salida__lte=fecha_salida)

    # models.Q permite buscar en nombre_bote O en fullname del cliente con un solo campo de texto
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

    from apps.embarcaciones.models import TipoBarco  # Import lazy para evitar circulares
    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj':        page_obj,
        'solicitudes':     page_obj.object_list,
        'titulo':          'Solicitudes pendientes',
        'estado_activo':   'PENDIENTE',              # Usado en solicitud_list.html para el tab activo
        'tipos_barco':     TipoBarco.objects.order_by('tipo_barco'),
        'q':               q,
        'tipo_id':         tipo_id,
        'primera_entrada': primera_entrada,
        'modo_fecha':      modo_fecha,
        'fecha_a':         fecha_a,
        'fecha_b':         fecha_b,
        'fecha_llegada':   fecha_llegada,
        'fecha_salida':    fecha_salida,
        'hay_filtros':     any([q, tipo_id, primera_entrada, fecha_a, fecha_b, fecha_llegada, fecha_salida]),
    })


# =============================================================================
# Vista: solicitud_en_espera_list
# Lista paginada (10/pág) de solicitudes EN_ESPERA (aprobadas por el admin
# pero aún sin espacio de muelle asignado).
# Soporta dos modos de orden:
#   'reciente' → más recientemente creadas primero (default)
#   'urgente'  → por fecha_llegada ascendente (las que llegan antes, primero)
# Usado en solicitud_list.html con estado_activo='EN_ESPERA'.
#
# Consumido por:
#   - templates/solicitudes/solicitud_list.html  (estado_activo='EN_ESPERA')
#   - templates/components/navbar.html           (enlace "En espera")
# =============================================================================
@login_required
def solicitud_en_espera_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='EN_ESPERA').order_by('-fecha_solicitud', '-id')

    q           = request.GET.get('q', '').strip()
    tipo_id     = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    orden       = request.GET.get('orden', 'reciente')

    # 'urgente': prioriza las que llegan antes para asignarles espacio con anticipación
    if orden == 'urgente':
        qs = qs.order_by('fecha_llegada', '-id')
    else:
        qs = qs.order_by('-fecha_solicitud', '-id')

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
        'orden':         orden,
        'hay_filtros':   any([q, tipo_id, fecha_desde, fecha_hasta]),
    })


# =============================================================================
# Vista: solicitud_aprobadas_list
# Lista paginada (10/pág) de solicitudes APROBADAS (embarcaciones actualmente
# en la marina con espacio asignado).
# Al inicio llama a _auto_completar() para transitar a COMPLETADA las vencidas,
# luego vuelve a filtrar por APROBADA para excluirlas del resultado.
# Permite filtrar por muelle activo (vía asignaciones__muelle_id).
#
# Consumido por:
#   - templates/solicitudes/solicitud_aprobadas.html
#   - templates/components/navbar.html  (enlace "Asignadas")
# =============================================================================
@login_required
def solicitud_aprobadas_list(request):
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='APROBADA')

    # Completa vencidas antes de mostrar el listado
    _auto_completar(qs)
    qs = qs.filter(estado='APROBADA')  # Re-filtra para excluir las recién completadas

    q                  = request.GET.get('q', '').strip()
    muelle_id          = request.GET.get('muelle', '')
    fecha_salida_desde = request.GET.get('fecha_salida_desde', '')
    fecha_salida_hasta = request.GET.get('fecha_salida_hasta', '')
    orden              = request.GET.get('orden', 'salida')
    tipo_id            = request.GET.get('tipo', '')

    if tipo_id:
        qs = qs.filter(embarcacion__tipo_barco_id=tipo_id)

    if q:
        qs = qs.filter(
            models.Q(embarcacion__nombre_bote__icontains=q) |
            models.Q(embarcacion__cliente__fullname__icontains=q)
        )

    # Filtra por muelle atravesando la relación Solicitud → Asignacion → Muelle.
    # distinct() es necesario porque el JOIN con asignaciones puede duplicar filas.
    if muelle_id:
        qs = qs.filter(asignaciones__muelle_id=muelle_id, asignaciones__activa=True).distinct()

    if fecha_salida_desde and fecha_salida_hasta:
        qs = qs.filter(fecha_salida__range=[fecha_salida_desde, fecha_salida_hasta])
    elif fecha_salida_desde:
        qs = qs.filter(fecha_salida=fecha_salida_desde)
    elif fecha_salida_hasta:
        qs = qs.filter(fecha_salida=fecha_salida_hasta)

    # 'salida': las que salen más pronto arriba (más urgente de atender)
    # 'llegada': las que llegaron más recientemente arriba
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
        'page_obj':           page_obj,
        'solicitudes':        page_obj.object_list,
        'titulo':             'Asignadas — en marina',
        'estado_activo':      'APROBADA',
        'muelles':            Muelle.objects.filter(estado=True).order_by('nombre'),
        'q':                  q,
        'muelle_id':          muelle_id,
        'fecha_salida_desde': fecha_salida_desde,
        'fecha_salida_hasta': fecha_salida_hasta,
        'orden':              orden,
        'tipos_barco':        TipoBarco.objects.order_by('tipo_barco'),
        'tipo_id':            tipo_id,
        'hay_filtros':        any([q, muelle_id, tipo_id, fecha_salida_desde, fecha_salida_hasta]),
    })


# =============================================================================
# Vista: solicitud_update
# GET: muestra solicitud_form.html pre-cargado con los datos actuales de la
#      solicitud, su embarcación y su cliente.
# POST: edita en cascada Cliente → Embarcacion → Solicitud dentro de
#       transaction.atomic(). Llama full_clean() en cada objeto para ejecutar
#       las validaciones del modelo antes de guardar.
#       Si hay error, vuelve al formulario con context['errors'].
#       Si tiene éxito, redirige al listado correspondiente al estado actual
#       de la solicitud.
#
# Consumido por:
#   - templates/solicitudes/solicitud_form.html
#   - templates/solicitudes/solicitud_list.html     (botón "Editar")
#   - templates/solicitudes/solicitud_aprobadas.html (botón "Editar")
# =============================================================================
@login_required
def solicitud_update(request, pk):
    from apps.embarcaciones.models import TipoBarco
    solicitud   = get_object_or_404(
        Solicitud.objects.select_related('embarcacion__cliente', 'embarcacion__tipo_barco'),
        pk=pk
    )
    tipos_barco = TipoBarco.objects.order_by('tipo_barco')
    context     = {'solicitud': solicitud, 'tipos_barco': tipos_barco}

    if request.method == 'POST':
        try:
            from django.db import transaction
            with transaction.atomic():
                # 1. Actualiza el cliente de la embarcación
                cliente          = solicitud.embarcacion.cliente
                cliente.fullname = request.POST.get('cliente_fullname', '').strip()
                cliente.email    = request.POST.get('cliente_email', '').strip().lower()
                cliente.telefono = request.POST.get('cliente_telefono', '').strip()
                cliente.full_clean()
                cliente.save()

                # 2. Actualiza la embarcación
                emb               = solicitud.embarcacion
                emb.nombre_bote   = request.POST.get('nombre_bote', '').strip()
                emb.tipo_barco_id = request.POST.get('tipo_barco')
                emb.eslora        = request.POST.get('eslora')
                emb.manga         = request.POST.get('manga')
                emb.calado        = request.POST.get('calado')
                emb.full_clean()
                emb.save()

                # 3. Actualiza la solicitud
                solicitud.fecha_llegada          = request.POST.get('fecha_llegada')
                solicitud.fecha_salida           = request.POST.get('fecha_salida')
                solicitud.comentario             = request.POST.get('comentario', '').strip()
                solicitud.primera_entrada_mexico = request.POST.get('primera_entrada_mexico') == 'on'
                solicitud.full_clean()
                solicitud.save()

            messages.success(request, 'Solicitud actualizada correctamente.')
            # Redirige al listado del estado actual para no perder el contexto del usuario
            destinos = {
                'PENDIENTE':  'solicitud_list',
                'EN_ESPERA':  'solicitud_en_espera_list',
                'APROBADA':   'solicitud_aprobadas_list',
                'COMPLETADA': 'solicitud_list',
                'RECHAZADA':  'solicitud_list',
            }
            return redirect(destinos.get(solicitud.estado, 'solicitud_list'))

        except ValidationError as exc:
            context['errors'] = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
        except Exception as exc:
            context['errors'] = [str(exc)]

    return render(request, 'solicitudes/solicitud_form.html', context)


# =============================================================================
# Vista: solicitud_cambiar_estado
# Acción POST que avanza o rechaza el estado de una solicitud.
# Solo acepta POST (@require_POST).
#
# Flujo para RECHAZADA:
#   1. Valida que se recibió motivo_rechazo (obligatorio).
#   2. Desactiva las asignaciones activas (soft-delete) de la solicitud.
#   3. Guarda el motivo en MAYÚSCULAS.
#
# Para cualquier estado: llama full_clean() y save() para ejecutar la
# máquina de estados de Solicitud.clean() y registrar el historial.
#
# El campo 'origen' en el POST determina a qué listado se redirige:
#   'list'      → solicitud_list (PENDIENTE)
#   'en_espera' → solicitud_en_espera_list
#   'aprobadas' → solicitud_aprobadas_list
#
# Consumido por:
#   - templates/solicitudes/solicitud_list.html     (botones de acción por estado)
#   - templates/solicitudes/solicitud_aprobadas.html
#   - templates/components/modal_rechazo.html       (formulario de motivo de rechazo)
# =============================================================================
@login_required
@require_POST
def solicitud_cambiar_estado(request, pk, nuevo_estado):
    solicitud       = get_object_or_404(Solicitud, pk=pk)
    estados_validos = [e[0] for e in Solicitud.ESTADOS]

    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('solicitud_list')

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

    if nuevo_estado == 'RECHAZADA':
        # Desactiva asignaciones antes de cambiar el estado para que el mapa
        # libere los espacios ocupados inmediatamente
        from apps.asignaciones.models import Asignacion
        Asignacion.objects.filter(solicitud=solicitud, activa=True).update(activa=False)

    solicitud.estado = nuevo_estado
    try:
        solicitud.full_clean()  # Ejecuta la máquina de estados en Solicitud.clean()
        solicitud.save()        # Solicitud.save() registra el cambio en SolicitudHistorial
        messages.success(request, f'Estado actualizado a {solicitud.get_estado_display()}.')
    except ValidationError as exc:
        for error in (exc.messages if hasattr(exc, 'messages') else [str(exc)]):
            messages.error(request, error)

    origen = request.POST.get('origen', 'list')
    # El destino de la redirección depende del nuevo estado y del origen de la petición
    destinos = {
        'PENDIENTE':  'solicitud_list',
        'EN_ESPERA':  'solicitud_en_espera_list',
        'APROBADA':   'solicitud_aprobadas_list',
        'RECHAZADA':  'solicitud_en_espera_list' if origen == 'en_espera' else 'solicitud_aprobadas_list' if origen == 'aprobadas' else 'solicitud_list',
        'COMPLETADA': 'solicitud_aprobadas_list',
    }
    return redirect(destinos.get(nuevo_estado, 'solicitud_list'))


# =============================================================================
# Vista: solicitud_detalle_json
# API GET que devuelve todos los datos de una solicitud y su historial de
# asignaciones en formato JSON. Usado por el popup de detalle en el CRUD de
# solicitudes aprobadas.
#
# Respuesta JSON incluye:
#   Datos de la solicitud: id, estado, fechas, comentario, primera_entrada_mexico
#   Datos de la embarcación: nombre_bote, tipo, eslora, manga, calado
#   Datos del cliente: fullname, email, telefono
#   asignaciones[]: historial completo de asignaciones con espacios, muelle,
#                   fechas y administrador responsable. activa=True indica la vigente.
#
# Consumido por:
#   - templates/components/popup_solicitud.html  (fetch GET al hacer clic en una fila)
# =============================================================================
@login_required
def solicitud_detalle_json(request, pk):
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'embarcacion__cliente',
            'embarcacion__tipo_barco',
        ), pk=pk
    )

    # Trae todas las asignaciones (activas e históricas) ordenadas: activa primero,
    # luego por fecha de asignación descendente
    asignaciones = solicitud.asignaciones.select_related(
        'muelle', 'administrador__user'
    ).prefetch_related('espacios').order_by('-activa', '-fecha_asignacion')

    asignaciones_data = []
    for a in asignaciones:
        # Construye lista de espacios para cada asignación
        espacios = [
            {'numero': e.numero, 'muelle': e.muelle.nombre}
            for e in a.espacios.all()  # prefetch_related evita N+1
        ]
        asignaciones_data.append({
            'id':               a.pk,
            'muelle':           a.muelle.nombre,
            'espacios':         espacios,
            'fecha_inicio':     a.fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_fin':        a.fecha_fin.strftime('%d/%m/%Y'),
            'fecha_asignacion': a.fecha_asignacion.strftime('%d/%m/%Y %H:%M') if a.fecha_asignacion else '—',
            'administrador':    str(a.administrador),  # Usa Administrador.__str__ → nombre completo
            'activa':           a.activa,
        })

    return JsonResponse({
        'id':                     solicitud.pk,
        'embarcacion':            solicitud.embarcacion.nombre_bote,
        'cliente':                solicitud.embarcacion.cliente.fullname,
        'tipo':                   solicitud.embarcacion.tipo_barco.tipo_barco,
        'eslora':                 float(solicitud.embarcacion.eslora),
        'manga':                  float(solicitud.embarcacion.manga),
        'calado':                 float(solicitud.embarcacion.calado),
        'fecha_llegada':          solicitud.fecha_llegada.strftime('%d/%m/%Y'),
        'fecha_salida':           solicitud.fecha_salida.strftime('%d/%m/%Y'),
        'fecha_solicitud':        solicitud.fecha_solicitud.strftime('%d/%m/%Y'),
        'estado':                 solicitud.get_estado_display(),  # Texto legible, no código
        'comentario':             solicitud.comentario or '',
        'email_cliente':          solicitud.embarcacion.cliente.email,
        'telefono_cliente':       solicitud.embarcacion.cliente.telefono,
        'primera_entrada_mexico': solicitud.primera_entrada_mexico,
        'asignaciones':           asignaciones_data,
    })