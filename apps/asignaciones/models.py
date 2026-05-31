# =============================================================================
# models.py — App: asignaciones
# Define los modelos de base de datos para administradores del sistema y las
# asignaciones de muelles/espacios a solicitudes de embarcaciones.
#
# Modelos exportados:
#   - Administrador  → usado en: apps/solicitudes/views.py,
#                                apps/usuarios/views.py,
#                                apps/mapa/views.py,
#                                admin.py (este mismo módulo),
#                                templates/components/navbar.html,
#                                templates/inicio.html,
#                                templates/usuarios/usuario_list.html
#   - Asignacion     → usado en: apps/solicitudes/views.py,
#                                apps/mapa/views.py,
#                                admin.py (este mismo módulo),
#                                templates/solicitudes/solicitud_aprobadas.html,
#                                templates/components/popup_solicitud.html,
#                                templates/mapa/mapa_component.html
# =============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.solicitudes.models import Solicitud  # Modelo de solicitud de embarcación al que se vincula una asignación
from apps.muelles.models import Muelle, Espacio  # Muelle y sus espacios físicos que se asignan


# -----------------------------------------------------------------------------
# Modelo: Administrador
# Perfil extendido del usuario de Django (User) que opera el sistema MARE.
# Cada usuario del sistema tiene exactamente un Administrador asociado (OneToOne).
# Distingue dos roles: gerente (acceso total) y empleado (acceso limitado).
# -----------------------------------------------------------------------------
class Administrador(models.Model):
    # Constantes de rol — usadas en comparaciones y en la lista de choices del campo `rol`
    ROL_GERENTE  = 'gerente'
    ROL_EMPLEADO = 'empleado'
    ROLES = [
        (ROL_GERENTE,  'Gerente'),
        (ROL_EMPLEADO, 'Empleado'),
    ]

    # Indica si el administrador está activo en el sistema. Usado en navbar.html
    # y en views de usuarios para filtrar quiénes pueden iniciar sesión u operar.
    activo = models.BooleanField(default=True)

    # Relación 1-a-1 con el usuario de Django. Al eliminar el User se elimina este perfil.
    # El related_name='administrador' permite acceder desde un User como: user.administrador
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='administrador'
    )
    # Rol del administrador dentro del sistema ('gerente' o 'empleado')
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_EMPLEADO)

    def es_gerente(self):
        """Retorna True si el administrador tiene rol de gerente. Usado en templates
        y vistas para controlar acceso a funciones exclusivas de gerencia
        (ej: navbar.html, inicio.html)."""
        return self.rol == self.ROL_GERENTE

    def save(self, *args, **kwargs):
        """Sobreescribe el guardado para normalizar los datos del User asociado:
        - first_name, last_name y username se convierten a MAYÚSCULAS
        - email se convierte a minúsculas (convención estándar)
        Llama a user.save() antes de super().save() para persistir ambos objetos."""
        if self.user:
            self.user.first_name = self.user.first_name.upper()
            self.user.last_name  = self.user.last_name.upper()
            self.user.username   = self.user.username.upper()
            self.user.email      = self.user.email.lower()  # por convención email siempre va en minúsculas
            self.user.save()
        super().save(*args, **kwargs)

    class Meta:
        db_table            = 'administrador'
        verbose_name        = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        # Muestra nombre completo si existe, de lo contrario el username.
        # Usado en el panel de admin y en dropdowns de selección.
        return self.user.get_full_name() or self.user.username


# -----------------------------------------------------------------------------
# Modelo: Asignacion
# Representa la asignación formal de un muelle y uno o varios espacios a una
# solicitud de embarcación, en un rango de fechas determinado.
# Un administrador es responsable de registrar la asignación.
#
# Relaciones clave:
#   - solicitud   → apps.solicitudes.Solicitud  (CASCADE: si se borra la solicitud, se borra la asignación)
#   - muelle      → apps.muelles.Muelle         (PROTECT: no se puede borrar un muelle con asignaciones)
#   - administrador → Administrador             (PROTECT: no se puede borrar un admin con asignaciones)
#   - espacios    → ManyToMany a Espacio        (una asignación puede ocupar varios espacios del muelle)
#
# Usado en templates:
#   - templates/solicitudes/solicitud_aprobadas.html  (listado de asignaciones activas)
#   - templates/components/popup_solicitud.html       (detalle de asignación de una solicitud)
#   - templates/mapa/mapa_component.html              (muestra espacios ocupados en el mapa)
# -----------------------------------------------------------------------------
class Asignacion(models.Model):
    # FK a Solicitud. Si la solicitud es eliminada, sus asignaciones también se eliminan.
    # related_name='asignaciones' permite acceder como: solicitud.asignaciones.all()
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="asignaciones"
    )
    # FK a Muelle. PROTECT impide borrar un muelle que tenga asignaciones vigentes.
    # related_name='asignaciones' permite: muelle.asignaciones.all()
    muelle = models.ForeignKey(
        Muelle,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )
    # FK al Administrador que registró la asignación.
    # related_name='asignaciones' permite: administrador.asignaciones.all()
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )

    # Timestamp automático del momento exacto en que se creó el registro de asignación
    fecha_asignacion = models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de asignación')

    # Rango de fechas en que la embarcación ocupa el muelle/espacios
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    # Una asignación puede ocupar uno o varios espacios simultáneamente
    # related_name='asignaciones' en Espacio permite: espacio.asignaciones.all()
    espacios = models.ManyToManyField(
        Espacio,
        related_name='asignaciones',
        blank=False,
    )

    # Permite desactivar una asignación sin eliminarla (soft-delete lógico).
    # Las consultas de traslape solo consideran asignaciones con activa=True.
    activa = models.BooleanField(default=True)


    class Meta:
        db_table = 'asignacion'
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"
        ordering            = ['-fecha_inicio']  # Las más recientes primero en listados

    def clean(self):
        """Validaciones de integridad de fechas y estado del muelle.
        Ejecutado automáticamente por Django al llamar full_clean() o desde el admin.
        - Verifica que fecha_fin sea posterior a fecha_inicio
        - Verifica que el muelle esté activo (estado=True)
        - Verifica que las fechas estén dentro del rango permitido por la solicitud"""
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha fin debe ser posterior a la fecha inicio.")

        # muelle_id verifica que ya hay un muelle asignado antes de acceder a muelle.estado
        if self.muelle_id and not self.muelle.estado:
            raise ValidationError("No se puede asignar: el muelle está inactivo.")

        if self.solicitud_id:
            # La fecha de inicio no puede ser antes de que llegue la embarcación
            if self.fecha_inicio and self.fecha_inicio < self.solicitud.fecha_llegada:
                raise ValidationError("La fecha de inicio no puede ser anterior a la llegada de la solicitud.")

            # La fecha fin no puede extenderse más allá de la salida programada
            if self.fecha_fin and self.fecha_fin > self.solicitud.fecha_salida:
                raise ValidationError("La fecha fin no puede ser posterior a la salida de la solicitud.")

    def validar_traslape_espacios(self):
        """Verifica que ningún espacio seleccionado esté ocupado por otra asignación
        activa en el mismo rango de fechas. Debe llamarse manualmente desde la vista
        o el formulario antes de guardar (apps/solicitudes/views.py).
        Lanza ValidationError si detecta solapamiento."""
        espacios_ids = self.espacios.values_list('id', flat=True)
        # Busca asignaciones activas de los mismos espacios cuyo rango se solape con el actual
        traslapes = Asignacion.objects.filter(
            espacios__in=espacios_ids,
            fecha_inicio__lte=self.fecha_fin,   # la otra empieza antes de que esta termine
            fecha_fin__gte=self.fecha_inicio,   # la otra termina después de que esta empieza
            activa=True,  # ← ya tiene esto, pero verificar que esté
        ).exclude(pk=self.pk).distinct()  # excluye la propia asignación al editar

        if traslapes.exists():
            raise ValidationError(
                'Uno o más espacios ya están ocupados en esas fechas.'
            )


    def __str__(self):
        return f'Asignacion #{self.pk}'