from django.contrib import admin
from apps.muelles.models import Muelle
from django.db.models import Count

@admin.register(Muelle)
class MuelleAdmin(admin.ModelAdmin):
    list_display  = (
        'id', 'nombre', 'total_espacios', 'tam_maximo',
        'get_estado', 'get_asignaciones_activas',
    )
    list_filter   = ('estado',)
    search_fields = ('nombre',)
    ordering      = ('nombre',)
    readonly_fields = ('coordenada_x', 'coordenada_y')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _asignaciones=Count('asignaciones')
        )

    def get_estado(self, obj):
        return 'Activo' if obj.estado else 'Inactivo'
    get_estado.short_description = 'Estado'
    get_estado.admin_order_field = 'estado'

    def get_asignaciones_activas(self, obj):
        return obj._asignaciones
    get_asignaciones_activas.short_description = 'Asignaciones'
    get_asignaciones_activas.admin_order_field = '_asignaciones'