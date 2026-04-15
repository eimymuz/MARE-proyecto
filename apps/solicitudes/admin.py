from django.contrib import admin
from apps.solicitudes.models import Solicitud, SolicitudHistorial
from django.utils.html     import format_html

class HistorialInline(admin.TabularInline):
    # Muestra el historial dentro del detalle de la solicitud
    model          = SolicitudHistorial
    extra          = 0
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'fecha_cambio')
    can_delete     = False

    def has_add_permission(self, request, obj=None):
        return False  # el historial solo lo crea el sistema, nunca a mano


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display        = (
        'id', 'get_embarcacion', 'get_cliente',
        'fecha_llegada', 'fecha_salida',
        'get_estado_badge',
    )
    list_filter         = ('estado', 'fecha_llegada')
    search_fields       = (
        'embarcacion__nombre_bote',
        'embarcacion__cliente__fullname',
        'embarcacion__cliente__email',
    )
    list_select_related = ('embarcacion__cliente',)
    readonly_fields     = ('fecha_solicitud',)
    date_hierarchy      = 'fecha_llegada'
    ordering            = ('-fecha_solicitud',)
    inlines             = [HistorialInline]

    def get_embarcacion(self, obj):
        return obj.embarcacion.nombre_bote
    get_embarcacion.short_description = 'Embarcación'
    get_embarcacion.admin_order_field = 'embarcacion__nombre_bote'

    def get_cliente(self, obj):
        return obj.embarcacion.cliente.fullname
    get_cliente.short_description = 'Cliente'
    get_cliente.admin_order_field = 'embarcacion__cliente__fullname'

    def get_estado_badge(self, obj):
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
    get_estado_badge.admin_order_field = 'estado'


@admin.register(SolicitudHistorial)
class SolicitudHistorialAdmin(admin.ModelAdmin):
    list_display  = ('id', 'solicitud', 'estado_anterior', 'estado_nuevo', 'fecha_cambio')
    list_filter   = ('estado_nuevo',)
    search_fields = ('solicitud__id',)
    readonly_fields = ('solicitud', 'estado_anterior', 'estado_nuevo', 'fecha_cambio')
    ordering      = ('-fecha_cambio',)

    def has_add_permission(self, request):
        return False  # solo lectura — el sistema lo genera automáticamente

    def has_delete_permission(self, request, obj=None):
        return False  # el historial no se puede borrar manualmente