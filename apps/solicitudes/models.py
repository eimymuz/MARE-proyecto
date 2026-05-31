# =============================================================================
# models.py — App: solicitudes
# Define los dos modelos centrales del sistema: Solicitud (el pedido de ingreso
# a la marina) y SolicitudHistorial (auditoría de cada cambio de estado).
#
# Modelos exportados:
#   - Solicitud         → usado en casi todas las apps:
#       apps/asignaciones/models.py  (FK en Asignacion.solicitud)
#       apps/mapa/views.py           (asignar_espacio, disponibilidad_json, inicio)
#       apps/asistente/views.py      (consultas del chatbot)
#       apps/reportes/views.py       (todos los reportes y estadísticas)
#       apps/solicitudes/views.py    (CRUD completo)
#       apps/publico/views.py        (creación desde formulario público)
#       templates/solicitudes/solicitud_list.html
#       templates/solicitudes/solicitud_aprobadas.html
#       templates/solicitudes/solicitud_form.html
#       templates/components/popup_solicitud.html
#       templates/components/modal_rechazo.html
#
#   - SolicitudHistorial → usado en:
#       apps/mapa/views.py           (registro al asignar espacio)
#       apps/reportes/views.py       (calcular_fecha_resolucion)
#       admin.py (esta app)          (HistorialInline)
# =============================================================================

from django.db              import models
from django.core.exceptions import ValidationError
from django.utils.timezone  import localdate
from apps.embarcaciones.models import Embarcacion  # FK: cada solicitud pertenece a una embarcación


# -----------------------------------------------------------------------------
# Modelo: Solicitud
# Representa la petición formal de ingreso de una embarcación a la marina.
# Es el objeto central del sistema: atraviesa un ciclo de vida de estados
# controlado por clean() y registrado en SolicitudHistorial.
#
# Ciclo de vida de estados permitido:
#   PENDIENTE → EN_ESPERA → APROBADA → COMPLETADA
#                ↘ RECHAZADA (desde cualquier estado activo)
#
# Relaciones inversas clave:
#   solicitud.asignaciones.all()  → Asignaciones de esta solicitud (M2M con Espacio)
#   solicitud.historial.all()     → Entradas de SolicitudHistorial
# -----------------------------------------------------------------------------
class Solicitud(models.Model):
    # Constantes de estado disponibles en todo el sistema como Solicitud.ESTADOS
    ESTADOS = [
        ('PENDIENTE',  'Pendiente'),   # Recién creada, sin revisar
        ('EN_ESPERA',  'En espera'),   # Revisada y aprobada por el admin, sin espacio asignado aún
        ('APROBADA',   'Aprobada'),    # Tiene asignación activa de muelle/espacio
        ('COMPLETADA', 'Completada'),  # La embarcación ya salió (fecha_salida pasó)
        ('RECHAZADA',  'Rechazada'),   # Denegada con motivo de rechazo
    ]

    # FK a la embarcación que solicita ingreso. PROTECT: no se puede borrar una
    # embarcación que tenga solicitudes. related_name='solicitudes' permite:
    # embarcacion.solicitudes.all()
    embarcacion = models.ForeignKey(
        Embarcacion,
        on_delete=models.PROTECT,
        related_name="solicitudes"
    )

    # Fecha en que se creó la solicitud. auto_now_add=True → solo lectura después de crear.
    # Durante clean() en objetos nuevos este campo es None; por eso clean() usa localdate().
    fecha_solicitud = models.DateField(auto_now_add=True)

    # Rango de estancia solicitado. Validado en clean() contra hoy y entre sí.
    fecha_llegada = models.DateField()
    fecha_salida  = models.DateField()

    # Comentario opcional del cliente sobre la solicitud. Se normaliza a MAYÚSCULAS en save().
    comentario = models.CharField(max_length=200, blank=True, null=True)

    # Estado actual dentro del ciclo de vida. Controlado por clean() y save().
    # Las transiciones válidas están definidas en clean().
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")

    # Indica si es la primera vez que la embarcación entra a aguas mexicanas.
    # Visible en solicitud_list.html y solicitud_form.html como badge/checkbox.
    primera_entrada_mexico = models.BooleanField(default=False, verbose_name='Primera entrada a México')

    # Texto obligatorio cuando estado='RECHAZADA'. Registrado en mayúsculas.
    # Visible en popup_solicitud.html y modal_rechazo.html.
    motivo_rechazo = models.CharField(max_length=500, blank=True, null=True, verbose_name='Motivo de rechazo')

    class Meta:
        db_table            = 'solicitud'
        verbose_name        = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering            = ['-fecha_solicitud']  # Más recientes primero en todos los listados

    def clean(self):
        """Valida fechas y las transiciones de estado permitidas.
        Ejecutado por full_clean() (llamado en views y publico/views.py antes de save()).

        Validaciones de fecha:
          - Solo en creación (pk is None): fecha_llegada no puede ser anterior a hoy.
            fecha_solicitud usa auto_now_add y es None durante clean() en nuevos objetos;
            por eso se usa localdate() como referencia.
          - Siempre: fecha_salida debe ser posterior a fecha_llegada.

        Validaciones de transición de estado (solo al editar):
          - COMPLETADA y RECHAZADA son estados terminales: no se puede salir de ellos.
          - Máquina de estados:
              PENDIENTE  → EN_ESPERA | RECHAZADA
              EN_ESPERA  → APROBADA  | RECHAZADA
              APROBADA   → COMPLETADA| RECHAZADA
        """
        today = localdate()

        # Validación de fecha solo al crear (pk is None = nuevo registro)
        if self.pk is None:
            if self.fecha_llegada and self.fecha_llegada < today:
                raise ValidationError('La fecha de llegada no puede ser anterior a hoy.')

        if self.fecha_llegada and self.fecha_salida and self.fecha_salida <= self.fecha_llegada:
            raise ValidationError('La fecha de salida debe ser posterior a la de llegada.')

        # Validación de máquina de estados al editar
        if self.pk:
            anterior = Solicitud.objects.get(pk=self.pk)

            if anterior.estado != self.estado:
                if anterior.estado in ['COMPLETADA', 'RECHAZADA']:
                    raise ValidationError('Una solicitud completada o rechazada no puede cambiar de estado.')

                if anterior.estado == 'PENDIENTE' and self.estado not in ['EN_ESPERA', 'RECHAZADA']:
                    raise ValidationError('Pendiente solo puede pasar a En espera o Rechazada.')

                if anterior.estado == 'EN_ESPERA' and self.estado not in ['APROBADA', 'RECHAZADA']:
                    raise ValidationError('En espera solo puede pasar a Aprobada o Rechazada.')

                if anterior.estado == 'APROBADA' and self.estado not in ['COMPLETADA', 'RECHAZADA']:
                    raise ValidationError('Aprobada solo puede pasar a Completada o Rechazada.')

    def save(self, *args, **kwargs):
        """Normaliza el comentario a MAYÚSCULAS y registra automáticamente
        cada cambio de estado en SolicitudHistorial.

        Al crear (pk is None): crea un registro historial con estado_anterior=None.
        Al editar con cambio de estado: crea un registro historial con el estado anterior.
        Si el estado no cambia al editar, no crea historial.

        SolicitudHistorial está definido en este mismo archivo, por lo que no
        requiere import adicional."""
        if self.comentario:
            self.comentario = self.comentario.upper()

        estado_anterior = None
        es_nuevo        = self.pk is None

        if not es_nuevo:
            # Lee el estado actual de la BD antes de sobreescribirlo
            anterior        = Solicitud.objects.get(pk=self.pk)
            estado_anterior = anterior.estado

        super().save(*args, **kwargs)

        # Registra el historial después del save() para tener el pk disponible en objetos nuevos
        if es_nuevo:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=None,        # None indica que es la creación inicial
                estado_nuevo=self.estado,
            )
        elif estado_anterior != self.estado:
            SolicitudHistorial.objects.create(
                solicitud=self,
                estado_anterior=estado_anterior,
                estado_nuevo=self.estado,
            )

    def asignacion_activa(self):
        """Retorna la Asignacion activa de esta solicitud, o None si no tiene.
        Usado en templates (popup_solicitud.html, solicitud_aprobadas.html)
        para mostrar el muelle y espacios asignados actualmente."""
        return self.asignaciones.filter(activa=True).first()

    def __str__(self):
        return f"Solicitud #{self.id} - {self.embarcacion.nombre_bote}"


# -----------------------------------------------------------------------------
# Modelo: SolicitudHistorial
# Registro de auditoría inmutable de cada cambio de estado de una Solicitud.
# Se crea automáticamente desde Solicitud.save() — nunca manualmente.
#
# Permite a reportes/views.py calcular la fecha_resolucion (fecha del último
# cambio a estado final: APROBADA, RECHAZADA o COMPLETADA).
#
# Relación inversa:
#   solicitud.historial.all() → todos los registros de esta solicitud
#   (usada en reportes/views.py con prefetch_related('historial'))
# -----------------------------------------------------------------------------
class SolicitudHistorial(models.Model):
    # FK a la Solicitud. CASCADE: si se borra la solicitud, se borra su historial.
    # related_name='historial' permite: solicitud.historial.all()
    solicitud = models.ForeignKey(
        "Solicitud",
        on_delete=models.CASCADE,
        related_name="historial"
    )

    # Estado antes del cambio. Null en la creación inicial de la solicitud.
    estado_anterior = models.CharField(max_length=50, blank=True, null=True)

    # Estado después del cambio. Nunca nulo.
    estado_nuevo    = models.CharField(max_length=50)

    # Timestamp automático del momento exacto del cambio de estado.
    # Usado en reportes como fecha_resolucion para filtrar por mes/año.
    fecha_cambio    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'solicitud_historial'
        verbose_name        = 'Historial de solicitud'
        verbose_name_plural = 'Historial de solicitudes'
        ordering            = ['-fecha_cambio']  # El más reciente primero

    def __str__(self):
        return f"Solicitud {self.solicitud.id}: {self.estado_anterior} -> {self.estado_nuevo}"