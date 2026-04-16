from django.contrib import admin
from apps.asignaciones.models import Asignacion, Administrador

@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display   = (
        'id',
        'get_embarcacion',
        'muelle',
        'fecha_inicio',
        'fecha_fin',
        'administrador',
    )
    list_filter    = ('muelle', 'fecha_inicio')
    search_fields  = (
        'solicitud__embarcacion__nombre_bote',
        'muelle__nombre',
    )
    # Evita N+1 queries en el listado
    list_select_related = ('solicitud__embarcacion', 'muelle', 'administrador__user')
    date_hierarchy = 'fecha_inicio'
    ordering       = ('-fecha_inicio',)

    def get_embarcacion(self, obj):
        return obj.solicitud.embarcacion.nombre_bote
    get_embarcacion.short_description = 'Embarcación'
    get_embarcacion.admin_order_field = 'solicitud__embarcacion__nombre_bote'