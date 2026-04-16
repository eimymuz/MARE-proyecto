from django.contrib import admin
from apps.embarcaciones.models import TipoBarco, Embarcacion

@admin.register(TipoBarco)
class TipoBarcoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'tipo_barco', 'get_total_embarcaciones')
    search_fields = ('tipo_barco',)
    ordering      = ('tipo_barco',)

    def get_queryset(self, request):
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            _total=Count('embarcaciones')
        )

    def get_total_embarcaciones(self, obj):
        return obj._total
    get_total_embarcaciones.short_description = 'Embarcaciones'
    get_total_embarcaciones.admin_order_field = '_total'


@admin.register(Embarcacion)
class EmbarcacionAdmin(admin.ModelAdmin):
    list_display        = (
        'id', 'nombre_bote', 'cliente', 'tipo_barco',
        'eslora', 'manga', 'calado',
    )
    list_filter         = ('tipo_barco',)
    search_fields       = (
        'nombre_bote',
        'cliente__fullname',
        'cliente__email',
    )
    list_select_related = ('cliente', 'tipo_barco')
    ordering            = ('nombre_bote',)