# =============================================================================
# admin.py — App: clientes
# Registra el modelo Cliente en el panel de administración de Django.
# Configura columnas, búsqueda y un campo calculado con total de embarcaciones.
# =============================================================================

from django.contrib import admin
from apps.clientes.models import Cliente  # Modelo definido en models.py de esta app


# -----------------------------------------------------------------------------
# ClienteAdmin
# Configuración del panel admin para el modelo Cliente.
# Muestra ID, nombre, email, teléfono y total de embarcaciones por cliente.
# El total de embarcaciones se calcula con una anotación SQL para evitar N+1.
# -----------------------------------------------------------------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Columnas del listado: incluye campo calculado get_total_embarcaciones
    list_display   = ('id', 'fullname', 'email', 'telefono', 'get_total_embarcaciones')
    # Campos de búsqueda en la barra del admin
    search_fields  = ('fullname', 'email', 'telefono')
    ordering       = ('fullname',)  # Orden alfabético por nombre

    def get_queryset(self, request):
        """Sobreescribe el queryset base para anotar cada Cliente con el conteo
        de sus embarcaciones en una sola query SQL (COUNT con GROUP BY).
        El alias _total_embarcaciones se usa en get_total_embarcaciones y
        como campo de ordenación (admin_order_field)."""
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            # 'embarcaciones' es el related_name definido en Embarcacion.cliente (FK)
            _total_embarcaciones=Count('embarcaciones')
        )

    def get_total_embarcaciones(self, obj):
        """Campo calculado que lee la anotación _total_embarcaciones del queryset.
        Evita hacer una query adicional por cada fila del listado."""
        return obj._total_embarcaciones
    get_total_embarcaciones.short_description = 'Embarcaciones'         # Encabezado de columna
    get_total_embarcaciones.admin_order_field = '_total_embarcaciones'  # Permite ordenar la columna