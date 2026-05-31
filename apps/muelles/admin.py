# =============================================================================
# admin.py — App: muelles
# Registra el modelo Muelle en el panel de administración de Django.
# Muestra estado activo/inactivo y total de asignaciones por muelle.
# Solo Muelle está registrado aquí; Espacio, ZonaTierra y EtiquetaMuelle
# se gestionan desde el admin pero no tienen clase Admin personalizada.
# =============================================================================

from django.contrib import admin
from apps.muelles.models import Muelle  # Modelo definido en models.py de esta app
from django.db.models import Count


# -----------------------------------------------------------------------------
# MuelleAdmin
# Configuración del panel admin para el modelo Muelle.
# Las coordenadas son readonly porque se gestionan desde el editor del mapa,
# no manualmente.
# -----------------------------------------------------------------------------
@admin.register(Muelle)
class MuelleAdmin(admin.ModelAdmin):
    # Columnas del listado: ID, nombre, espacios totales, tamaño máximo,
    # estado legible (calculado) y total de asignaciones históricas (calculado)
    list_display  = (
        'id', 'nombre', 'total_espacios', 'tam_maximo',
        'get_estado', 'get_asignaciones_activas',
    )
    list_filter   = ('estado',)  # Filtro lateral para ver solo muelles activos o inactivos
    search_fields = ('nombre',)
    ordering      = ('nombre',)
    # Las coordenadas se asignan desde el editor visual del mapa; no deben editarse a mano
    readonly_fields = ('coordenada_x', 'coordenada_y')

    def get_queryset(self, request):
        """Anota cada Muelle con el conteo total de asignaciones usando un JOIN,
        evitando una query adicional por cada fila del listado."""
        return super().get_queryset(request).annotate(
            # 'asignaciones' es el related_name de la FK en Asignacion.muelle
            _asignaciones=Count('asignaciones')
        )

    def get_estado(self, obj):
        """Convierte el booleano estado a texto legible para el listado del admin."""
        return 'Activo' if obj.estado else 'Inactivo'
    get_estado.short_description = 'Estado'
    get_estado.admin_order_field = 'estado'  # Permite ordenar la columna por el campo real

    def get_asignaciones_activas(self, obj):
        """Lee la anotación _asignaciones calculada en get_queryset.
        Muestra el total histórico de asignaciones del muelle (no solo las activas)."""
        return obj._asignaciones
    get_asignaciones_activas.short_description = 'Asignaciones'
    get_asignaciones_activas.admin_order_field = '_asignaciones'