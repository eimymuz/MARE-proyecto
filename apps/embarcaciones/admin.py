# =============================================================================
# admin.py — App: embarcaciones
# Registra TipoBarco y Embarcacion en el panel de administración de Django.
# Configura columnas, filtros, búsqueda y campos calculados para cada modelo.
# =============================================================================

from django.contrib import admin
from apps.embarcaciones.models import TipoBarco, Embarcacion  # Modelos de models.py de esta app


# -----------------------------------------------------------------------------
# TipoBarcoAdmin
# Configuración del admin para el catálogo de tipos de barco.
# Muestra cuántas embarcaciones hay de cada tipo usando una anotación SQL,
# lo que evita hacer una query extra por cada fila (N+1).
# -----------------------------------------------------------------------------
@admin.register(TipoBarco)
class TipoBarcoAdmin(admin.ModelAdmin):
    # Columnas del listado: ID, nombre del tipo y total de embarcaciones (calculado)
    list_display  = ('id', 'tipo_barco', 'get_total_embarcaciones')
    search_fields = ('tipo_barco',)
    ordering      = ('tipo_barco',)

    def get_queryset(self, request):
        """Anota cada TipoBarco con el conteo de sus embarcaciones en una sola
        query SQL. El alias _total se usa en get_total_embarcaciones y como
        campo de ordenación de la columna en el admin."""
        from django.db.models import Count
        return super().get_queryset(request).annotate(
            # 'embarcaciones' es el related_name de la FK en Embarcacion.tipo_barco
            _total=Count('embarcaciones')
        )

    def get_total_embarcaciones(self, obj):
        """Lee la anotación _total calculada en get_queryset. Sin la anotación
        habría una query adicional por cada tipo en el listado."""
        return obj._total
    get_total_embarcaciones.short_description = 'Embarcaciones'  # Encabezado de columna
    get_total_embarcaciones.admin_order_field = '_total'          # Permite ordenar la columna


# -----------------------------------------------------------------------------
# EmbarcacionAdmin
# Configuración del admin para el modelo Embarcacion.
# Muestra los datos clave de cada embarcación y permite filtrar por tipo.
# Usa select_related para evitar N+1 al mostrar cliente y tipo_barco.
# -----------------------------------------------------------------------------
@admin.register(Embarcacion)
class EmbarcacionAdmin(admin.ModelAdmin):
    # Columnas del listado: ID, nombre del bote, cliente propietario,
    # tipo de barco y las tres dimensiones físicas
    list_display        = (
        'id', 'nombre_bote', 'cliente', 'tipo_barco',
        'eslora', 'manga', 'calado',
    )
    # Filtro lateral para acotar resultados por tipo de embarcación
    list_filter         = ('tipo_barco',)
    # Búsqueda por nombre del bote, nombre del cliente o su email
    search_fields       = (
        'nombre_bote',
        'cliente__fullname',
        'cliente__email',
    )
    # Trae cliente y tipo_barco en un solo JOIN para evitar N+1 en el listado
    list_select_related = ('cliente', 'tipo_barco')
    ordering            = ('nombre_bote',)  # Orden alfabético por nombre del bote