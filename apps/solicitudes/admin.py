# =============================================================================
# admin.py — App: solicitudes
# Registra Solicitud y SolicitudHistorial en el panel de administración.
# SolicitudHistorial se muestra también como inline dentro del detalle de
# cada Solicitud, y como listado de solo lectura independiente.
# =============================================================================

from django.contrib import admin
from apps.solicitudes.models import Solicitud, SolicitudHistorial
from django.utils.html import format_html  # Para renderizar HTML seguro en columnas del admin


# -----------------------------------------------------------------------------
# HistorialInline
# Muestra el historial de cambios de estado de una Solicitud directamente
# en la página de edición de esa solicitud (TabularInline).
# Todos los campos son readonly porque el historial lo crea el sistema
# automáticamente desde Solicitud.save(); nunca debe editarse a mano.
# -----------------------------------------------------------------------------
class HistorialInline(admin.TabularInline):
    model           = SolicitudHistorial
    extra           = 0             # Sin filas vacías para nuevas entradas
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'fecha_cambio')
    can_delete      = False         # El historial es inmutable

    def has_add_permission(self, request, obj=None):
        return False  # El historial solo lo crea el sistema, nunca a mano


# -----------------------------------------------------------------------------
# SolicitudAdmin
# Panel admin para gestionar solicitudes.
# Muestra embarcación y cliente como columnas calculadas para evitar
# mostrar el ID de FK. El estado se renderiza como badge coloreado con HTML.
# Incluye HistorialInline para ver la trazabilidad de cambios de estado.
# -----------------------------------------------------------------------------
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    # Columnas del listado: id, embarcación (calculado), cliente (calculado),
    # fechas de estancia, estado como badge y motivo de rechazo si aplica
    list_display        = (
        'id', 'get_embarcacion', 'get_cliente',
        'fecha_llegada', 'fecha_salida',
        'get_estado_badge', 'motivo_rechazo',
    )
    list_filter         = ('estado', 'fecha_llegada')
    search_fields       = (
        'embarcacion__nombre_bote',
        'embarcacion__cliente__fullname',
        'embarcacion__cliente__email',
    )
    # Evita N+1 en el listado del admin para cliente y embarcación
    list_select_related = ('embarcacion__cliente',)
    # fecha_solicitud es auto_now_add: no debe editarse manualmente
    readonly_fields     = ('fecha_solicitud',)
    date_hierarchy      = 'fecha_llegada'   # Navegador de fechas jerárquico en el admin
    ordering            = ('-fecha_solicitud',)
    inlines             = [HistorialInline]  # Historial de cambios de estado al pie de cada solicitud

    def get_embarcacion(self, obj):
        """Campo calculado: nombre del bote de la embarcación asociada."""
        return obj.embarcacion.nombre_bote
    get_embarcacion.short_description = 'Embarcación'
    get_embarcacion.admin_order_field = 'embarcacion__nombre_bote'

    def get_cliente(self, obj):
        """Campo calculado: nombre completo del cliente propietario."""
        return obj.embarcacion.cliente.fullname
    get_cliente.short_description = 'Cliente'
    get_cliente.admin_order_field = 'embarcacion__cliente__fullname'

    def get_estado_badge(self, obj):
        """Renderiza el estado como un badge HTML con color de fondo y texto
        según el estado actual. Usa format_html para escapar el HTML de forma segura."""
        colores = {
            'PENDIENTE':  ('#FAEEDA', '#633806'),
            'EN_ESPERA':  ('#E6F1FB', '#0C447C'),
            'APROBADA':   ('#E1F5EE', '#085041'),
            'COMPLETADA': ('#E1F5EE', '#085041'),
            'RECHAZADA':  ('#FCEBEB', '#791F1F'),
        }
        bg, fg = colores.get(obj.estado, ('#eee', '#333'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:500">{}</span>',
            bg, fg, obj.get_estado_display()
        )
    get_estado_badge.short_description = 'Estado'
    get_estado_badge.admin_order_field = 'estado'  # Permite ordenar la columna por estado


# -----------------------------------------------------------------------------
# SolicitudHistorialAdmin
# Panel admin de solo lectura para auditar el historial de cambios de estado.
# No permite crear ni eliminar registros: el historial lo genera Solicitud.save().
# Útil para depuración y auditoría sin modificar datos.
# -----------------------------------------------------------------------------
@admin.register(SolicitudHistorial)
class SolicitudHistorialAdmin(admin.ModelAdmin):
    list_display    = ('id', 'solicitud', 'estado_anterior', 'estado_nuevo', 'fecha_cambio')
    list_filter     = ('estado_nuevo',)
    search_fields   = ('solicitud__id',)
    # Todos readonly: este registro nunca debe editarse manualmente
    readonly_fields = ('solicitud', 'estado_anterior', 'estado_nuevo', 'fecha_cambio')
    ordering        = ('-fecha_cambio',)

    def has_add_permission(self, request):
        return False  # Solo lectura — el sistema lo genera automáticamente

    def has_delete_permission(self, request, obj=None):
        return False  # El historial no se puede borrar manualmente