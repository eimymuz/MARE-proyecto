# =============================================================================
# admin.py — App: asignaciones
# Registra los modelos Administrador y Asignacion en el panel de administración
# de Django, configurando columnas, filtros y búsqueda para cada uno.
# =============================================================================

from django.contrib import admin
from apps.asignaciones.models import Asignacion, Administrador  # Modelos definidos en models.py de esta misma app


# -----------------------------------------------------------------------------
# AdministradorAdmin
# Configuración del panel admin para el modelo Administrador.
# Muestra el nombre completo y el usuario Django asociado.
# Permite buscar por username, nombre o apellido.
# -----------------------------------------------------------------------------
@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    # Columnas visibles en el listado del admin
    list_display  = ('__str__', 'user')
    # Campos por los que se puede buscar en la barra de búsqueda del admin
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


# -----------------------------------------------------------------------------
# AsignacionAdmin
# Configuración del panel admin para el modelo Asignacion.
# Muestra información clave de cada asignación con navegación por fechas.
# -----------------------------------------------------------------------------
@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    # Columnas del listado: ID, embarcación (campo calculado), muelle, fechas y administrador responsable
    list_display   = (
        'id',
        'get_embarcacion',
        'muelle',
        'fecha_inicio',
        'fecha_fin',
        'administrador',
    )
    # Filtros laterales en el admin para acotar resultados por muelle o fecha
    list_filter    = ('muelle', 'fecha_inicio')
    # Búsqueda por nombre de embarcación o nombre de muelle
    search_fields  = (
        'solicitud__embarcacion__nombre_bote',
        'muelle__nombre',
    )
    # Evita N+1 queries en el listado: trae en un solo JOIN los objetos relacionados
    list_select_related = ('solicitud__embarcacion', 'muelle', 'administrador__user')
    # Navegador de fechas jerárquico (año → mes → día) basado en fecha_inicio
    date_hierarchy = 'fecha_inicio'
    ordering       = ('-fecha_inicio',)  # Más recientes primero

    def get_embarcacion(self, obj):
        """Campo calculado que muestra el nombre de la embarcación de la solicitud.
        Accede a: Asignacion → Solicitud → Embarcacion → nombre_bote"""
        return obj.solicitud.embarcacion.nombre_bote
    get_embarcacion.short_description = 'Embarcación'          # Encabezado de columna en el admin
    get_embarcacion.admin_order_field = 'solicitud__embarcacion__nombre_bote'  # Permite ordenar la columna