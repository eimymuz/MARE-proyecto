# =============================================================================
# views.py — App: publico
# Vistas accesibles sin autenticación que forman el flujo de entrada al
# sistema para clientes externos (dueños de embarcaciones).
#
# Vistas:
#   landing          GET  /           → template: publico/landing.html
#   solicitud_submit POST /solicitar/ → JsonResponse
#
# Esta es la única app del proyecto que no requiere @login_required,
# ya que el cliente externo no tiene cuenta en el sistema.
#
# Modelos escritos:
#   apps.clientes.Cliente      (get_or_create por email)
#   apps.embarcaciones.Embarcacion (get_or_create por cliente + nombre_bote)
#   apps.solicitudes.Solicitud (creación nueva, estado inicial PENDIENTE)
#
# Modelos leídos:
#   apps.embarcaciones.TipoBarco (para poblar el select del formulario)
# =============================================================================

from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction  # Garantiza que los tres objetos se creen juntos o ninguno

from apps.embarcaciones.models import TipoBarco, Embarcacion
from apps.clientes.models import Cliente
from apps.solicitudes.models import Solicitud


# -----------------------------------------------------------------------------
# Vista: landing
# Renderiza la página pública de la marina sin requerir autenticación.
# Envía el queryset de TipoBarco al template para llenar el <select>
# del formulario de solicitud de ingreso.
#
# Contexto enviado a publico/landing.html:
#   tipos_barco → queryset de TipoBarco ordenado alfabéticamente
#                 Usado en el <select> de tipo de embarcación del formulario
# -----------------------------------------------------------------------------
def landing(request):
    tipos_barco = TipoBarco.objects.order_by('tipo_barco')

    return render(request, 'publico/landing.html', {
        'tipos_barco': tipos_barco
    })


# -----------------------------------------------------------------------------
# Vista: solicitud_submit
# Endpoint POST que procesa el formulario público de solicitud de ingreso.
# No requiere autenticación; es el punto de entrada de clientes externos.
#
# Flujo completo dentro de transaction.atomic():
#   1. get_or_create de Cliente usando email como clave de unicidad.
#      Si el cliente ya existe, se reutiliza sin modificar sus datos.
#   2. get_or_create de Embarcacion usando (cliente, nombre_bote) como clave.
#      Si la embarcación ya existe, se reutiliza con sus dimensiones originales.
#   3. Creación de una nueva Solicitud con estado='PENDIENTE'.
#      Se llama full_clean() antes de save() para ejecutar las validaciones
#      del modelo (fechas, estado del muelle, etc.).
#
# Si cualquiera de los tres pasos falla, transaction.atomic() hace rollback
# completo: no quedan registros huérfanos en la BD.
#
# Respuesta JSON exitosa:  {'ok': True, 'solicitud_id': N, 'email': '...'}
# Respuesta JSON de error: {'ok': False, 'error': '...'}
#
# Consumido por:
#   - templates/publico/landing.html  (fetch POST desde el formulario JS)
# -----------------------------------------------------------------------------
def solicitud_submit(request):
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    # ── Extracción de datos del formulario ────────────────────────────────────
    # .strip() elimina espacios accidentales; email va a minúsculas para
    # coincidir con la normalización de Cliente.save()
    fullname      = request.POST.get('fullname', '').strip()
    email         = request.POST.get('email', '').strip().lower()
    telefono      = request.POST.get('telefono', '').strip()

    nombre_bote   = request.POST.get('nombre_bote', '').strip()
    tipo_barco_id = request.POST.get('tipo_barco')

    eslora        = request.POST.get('eslora')
    manga         = request.POST.get('manga')
    calado        = request.POST.get('calado')

    fecha_llegada = request.POST.get('fecha_llegada')
    fecha_salida  = request.POST.get('fecha_salida')

    # primera_entrada_mexico es un checkbox; 'on' cuando está marcado
    primera_entrada = request.POST.get('primera_entrada_mexico') == 'on'
    comentario      = request.POST.get('comentario', '').strip()

    # ── Validación de presencia de campos obligatorios ───────────────────────
    # Verifica que ningún campo clave esté vacío o None antes de tocar la BD
    campos_obligatorios = [
        fullname, email, telefono,
        nombre_bote, tipo_barco_id,
        eslora, manga, calado,
        fecha_llegada, fecha_salida
    ]

    if not all(campos_obligatorios):
        return JsonResponse({
            'ok': False,
            'error': 'Completa todos los campos obligatorios.'
        })

    try:
        with transaction.atomic():

            # get_or_create busca por email (clave única de Cliente).
            # Si ya existe ese email, devuelve el Cliente existente sin modificarlo.
            # defaults se aplica SOLO al crear; los datos del cliente no se actualizan
            # si ya existe (un cliente recurrente conserva su nombre y teléfono previos).
            cliente, _ = Cliente.objects.get_or_create(
                email=email,
                defaults={
                    'fullname': fullname,
                    'telefono': telefono
                }
            )

            # get_or_create busca por (cliente, nombre_bote).
            # Permite que el mismo cliente tenga varias embarcaciones distintas.
            # Si la embarcación ya existe, se reutiliza con sus dimensiones guardadas
            # (un cliente no puede cambiar eslora/manga de una embarcación existente aquí).
            embarcacion, _ = Embarcacion.objects.get_or_create(
                cliente=cliente,
                nombre_bote=nombre_bote,
                defaults={
                    'tipo_barco_id': tipo_barco_id,
                    'eslora': eslora,
                    'manga': manga,
                    'calado': calado
                }
            )

            # Siempre se crea una nueva Solicitud (no get_or_create):
            # el mismo cliente puede solicitar ingreso múltiples veces con distintas fechas.
            # full_clean() ejecuta Solicitud.clean() antes de guardar en BD,
            # validando fechas y coherencia de datos.
            solicitud = Solicitud(
                embarcacion=embarcacion,
                fecha_llegada=fecha_llegada,
                fecha_salida=fecha_salida,
                comentario=comentario,
                primera_entrada_mexico=primera_entrada,
                estado='PENDIENTE'  # Estado inicial; cambia a EN_ESPERA o APROBADA por el admin
            )

            solicitud.full_clean()  # Lanza ValidationError si los datos no pasan clean()
            solicitud.save()

        # Devuelve solicitud_id y email para que landing.html pueda mostrar
        # un mensaje de confirmación personalizado al cliente
        return JsonResponse({
            'ok': True,
            'solicitud_id': solicitud.pk,
            'email': email
        })

    except ValidationError as exc:
        # Errores de validación del modelo (fechas inválidas, campos fuera de rango, etc.)
        mensajes = exc.messages if hasattr(exc, 'messages') else [str(exc)]
        return JsonResponse({
            'ok': False,
            'error': ' '.join(mensajes)
        })

    except Exception as exc:
        # Cualquier otro error inesperado (BD no disponible, constraint violation, etc.)
        return JsonResponse({
            'ok': False,
            'error': str(exc)
        })