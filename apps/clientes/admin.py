from django.contrib import admin
from apps.clientes.models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display   = ('id', 'fullname', 'email', 'telefono', 'get_total_embarcaciones')
    search_fields  = ('fullname', 'email', 'telefono')
    ordering       = ('fullname',)

    def get_queryset(self, request):
        # Anota el total de embarcaciones para evitar N+1
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            _total_embarcaciones=Count('embarcaciones')
        )

    def get_total_embarcaciones(self, obj):
        return obj._total_embarcaciones
    get_total_embarcaciones.short_description = 'Embarcaciones'
    get_total_embarcaciones.admin_order_field = '_total_embarcaciones'