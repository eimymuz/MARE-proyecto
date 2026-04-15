from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from apps.embarcaciones.models import TipoBarco, Embarcacion
from apps.clientes.models import Cliente
from apps.solicitudes.models import Solicitud


def landing(request):
    """Página pública principal del cliente."""
    tipos_barco = TipoBarco.objects.order_by('tipo_barco')
    return render(request, 'publico/landing.html', {'tipos_barco': tipos_barco})


def solicitud_submit(request):
    """Recibe el formulario público via POST y crea la solicitud."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    from django.db import transaction

    fullname        = request.POST.get('fullname', '').strip()
    email           = request.POST.get('email', '').strip().lower()
    telefono        = request.POST.get('telefono', '').strip()
    nombre_bote     = request.POST.get('nombre_bote', '').strip()
    tipo_barco_id   = request.POST.get('tipo_barco')
    eslora          = request.POST.get('eslora')
    manga           = request.POST.get('manga')
    calado          = request.POST.get('calado')
    fecha_llegada   = request.POST.get('fecha_llegada')
    fecha_salida    = request.POST.get('fecha_salida')
    primera_entrada = request.POST.get('primera_entrada_mexico') == 'on'
    comentario      = request.POST.get('comentario', '').strip()

    if not all([fullname, email, telefono, nombre_bote, tipo_barco_id,
                eslora, manga, calado, fecha_llegada, fecha_salida]):
        return JsonResponse({'ok': False, 'error': 'Completa todos los campos obligatorios.'})

    try:
        with transaction.atomic():
            cliente, _ = Cliente.objects.get_or_create(
                email=email,
                defaults={'fullname': fullname, 'telefono': telefono}
            )
            embarcacion, _ = Embarcacion.objects.get_or_create(
                cliente=cliente,
                nombre_bote=nombre_bote,
                defaults={
                    'tipo_barco_id': tipo_barco_id,
                    'eslora': eslora,
                    'manga':  manga,
                    'calado': calado,
                }
            )
            solicitud = Solicitud(
                embarcacion            = embarcacion,
                fecha_llegada          = fecha_llegada,
                fecha_salida           = fecha_salida,
                comentario             = comentario,
                primera_entrada_mexico = primera_entrada,
                estado                 = 'PENDIENTE',
            )
            solicitud.full_clean()
            solicitud.save()

        return JsonResponse({'ok': True, 'solicitud_id': solicitud.pk, 'email': email})

    except ValidationError as exc:
        msgs = exc.messages if hasattr(exc, 'messages') else [str(exc)]
        return JsonResponse({'ok': False, 'error': ' '.join(msgs)})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)})
