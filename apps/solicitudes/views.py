from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from .models import Solicitud


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
    """CRUD principal — muestra todas las solicitudes PENDIENTES."""
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='PENDIENTE').order_by('-fecha_solicitud', '-id')

    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj':    page_obj,
        'solicitudes': page_obj.object_list,
        'titulo':      'Solicitudes pendientes',
        'estado_activo': 'PENDIENTE',
    })


@login_required
def solicitud_en_espera_list(request):
    """Solicitudes EN_ESPERA — en negociación con el cliente."""
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='EN_ESPERA').order_by('-fecha_solicitud', '-id')

    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'solicitudes/solicitud_list.html', {
        'page_obj':      page_obj,
        'solicitudes':   page_obj.object_list,
        'titulo':        'Pendientes de asignación',
        'estado_activo': 'EN_ESPERA',
    })

@login_required
def solicitud_aprobadas_list(request):
    """Solicitudes APROBADAS — embarcaciones en la marina."""
    qs = Solicitud.objects.select_related(
        'embarcacion__cliente',
        'embarcacion__tipo_barco',
    ).filter(estado='APROBADA').order_by('-fecha_llegada', '-id')

    # auto-completar vencidas antes de mostrar
    _auto_completar(qs)

    # recargar tras posibles cambios
    qs = qs.filter(estado='APROBADA')

    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'solicitudes/solicitud_aprobadas.html', {
        'page_obj':      page_obj,
        'solicitudes':   page_obj.object_list,
        'titulo':        'Asignadas — en marina',
        'estado_activo': 'APROBADA',
    })


@login_required
def solicitud_detail(request, pk):
    solicitud = get_object_or_404(
        Solicitud.objects.select_related(
            'embarcacion__cliente',
            'embarcacion__tipo_barco',
        ), pk=pk
    )
    return render(request, 'solicitudes/solicitud_detail.html', {
        'solicitud':   solicitud,
        'historial':   solicitud.historial.order_by('-fecha_cambio'),
        'asignaciones': solicitud.asignaciones.select_related(
            'muelle', 'administrador__user'
        ).prefetch_related('espacios').order_by('-fecha_inicio'),
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
            return redirect('solicitud_detail', pk=solicitud.pk)

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
    solicitud      = get_object_or_404(Solicitud, pk=pk)
    estados_validos = [e[0] for e in Solicitud.ESTADOS]

    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('solicitud_detail', pk=pk)

    solicitud.estado = nuevo_estado
    try:
        solicitud.full_clean()
        solicitud.save()
        messages.success(request, f'Estado actualizado a {solicitud.get_estado_display()}.')
    except ValidationError as exc:
        for error in (exc.messages if hasattr(exc, 'messages') else [str(exc)]):
            messages.error(request, error)

    destinos = {
        'PENDIENTE':  'solicitud_list',
        'EN_ESPERA':  'solicitud_list',  # ← se queda en solicitudes
        'APROBADA':   'solicitud_aprobadas_list',
        'RECHAZADA':  'solicitud_list',
        'COMPLETADA': 'solicitud_list',
    }
    nombre = destinos.get(nuevo_estado)
    if nombre in ['solicitud_list', 'solicitud_en_espera_list', 'solicitud_aprobadas_list']:
        return redirect(nombre)
    return redirect('solicitud_detail', pk=pk)


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
        'id':           solicitud.pk,
        'embarcacion':  solicitud.embarcacion.nombre_bote,
        'cliente':      solicitud.embarcacion.cliente.fullname,
        'tipo':         solicitud.embarcacion.tipo_barco.tipo_barco,
        'eslora':       float(solicitud.embarcacion.eslora),
        'manga':        float(solicitud.embarcacion.manga),
        'calado':       float(solicitud.embarcacion.calado),
        'fecha_llegada':solicitud.fecha_llegada.strftime('%d/%m/%Y'),
        'fecha_salida': solicitud.fecha_salida.strftime('%d/%m/%Y'),
        'estado':       solicitud.get_estado_display(),
        'comentario':   solicitud.comentario or '',
        'asignaciones': asignaciones_data,
        'email_cliente': solicitud.embarcacion.cliente.email,
    })