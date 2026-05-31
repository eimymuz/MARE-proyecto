# =============================================================================
# models.py — App: embarcaciones
# Define los modelos TipoBarco y Embarcacion, que representan el catálogo
# de tipos de barco y las embarcaciones concretas registradas por los clientes.
#
# Modelos exportados:
#   - TipoBarco   → usado en:
#       apps/embarcaciones/admin.py       (gestión en panel admin)
#       apps/publico/views.py             (campo del formulario de solicitud)
#       apps/solicitudes/models.py        (acceso vía Embarcacion.tipo_barco)
#       apps/asistente/views.py           (filtro por tipo en consultas del chatbot)
#       templates/solicitudes/solicitud_form.html   (dropdown de tipo de barco)
#       templates/reporte/estadisticas.html         (gráficas por tipo de barco)
#       templates/reporte/reporte_estadisticas_pdf.html
#
#   - Embarcacion → usado en:
#       apps/solicitudes/models.py        (FK: Solicitud.embarcacion)
#       apps/publico/views.py             (get_or_create al crear solicitud)
#       apps/mapa/views.py                (datos de embarcación en el mapa)
#       apps/asignaciones/admin.py        (nombre de la embarcación en listado)
#       apps/asistente/views.py           (nombre_bote en respuestas del chatbot)
#       templates/solicitudes/solicitud_list.html
#       templates/solicitudes/solicitud_aprobadas.html
#       templates/components/popup_solicitud.html
#       templates/mapa/mapa_component.html
#       templates/reporte/reporte.html / reporte_pdf.html
# =============================================================================

from django.db import models
from django.core.exceptions import ValidationError
from apps.clientes.models import Cliente  # FK: cada embarcación pertenece a un cliente


# -----------------------------------------------------------------------------
# Modelo: TipoBarco
# Catálogo de tipos de embarcación (ej: VELERO, YATE, CATAMARÁN, LANCHA).
# Se gestiona desde el panel admin. El chatbot (asistente/views.py) lo usa
# para filtrar solicitudes por tipo usando icontains sobre este campo.
# -----------------------------------------------------------------------------
class TipoBarco(models.Model):
    # Nombre del tipo de barco. Se normaliza a MAYÚSCULAS en save().
    # Usado como etiqueta en formularios (solicitud_form.html) y filtros del chatbot.
    tipo_barco = models.CharField(max_length=80)

    class Meta:
        db_table            = 'tipo_barco'
        verbose_name        = 'Tipo de barco'
        verbose_name_plural = 'Tipos de barco'
        ordering            = ['tipo_barco']  # Ordenado alfabéticamente en dropdowns

    def save(self, *args, **kwargs):
        """Normaliza el nombre del tipo a MAYÚSCULAS antes de guardar,
        para consistencia con la búsqueda icontains del asistente."""
        if self.tipo_barco:
            self.tipo_barco = self.tipo_barco.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        # Representación usada en el admin, dropdowns y relaciones __str__
        return self.tipo_barco


# -----------------------------------------------------------------------------
# Modelo: Embarcacion
# Representa una embarcación específica registrada en el sistema.
# Pertenece a un Cliente y tiene un TipoBarco.
# Las dimensiones (eslora, manga, calado) son validadas en clean() para
# garantizar valores físicamente posibles.
#
# Relaciones inversas clave:
#   embarcacion.solicitudes.all()  → todas las Solicitudes de esta embarcación
#   (definida por related_name en apps/solicitudes/models.py)
# -----------------------------------------------------------------------------
class Embarcacion(models.Model):
    # FK al Cliente propietario. PROTECT evita borrar un cliente con embarcaciones registradas.
    # related_name='embarcaciones' permite acceder como: cliente.embarcaciones.all()
    # Usado en: ClienteAdmin (conteo), publico/views.py (get_or_create), mapa, reportes.
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )
    # FK al tipo de embarcación. PROTECT impide borrar un tipo que tenga embarcaciones.
    # related_name='embarcaciones' permite: tipo_barco.embarcaciones.all()
    # Usado en: solicitud_form.html (dropdown), asistente (filtro por tipo), reportes.
    tipo_barco = models.ForeignKey(
        TipoBarco,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )

    # Nombre del bote. Se normaliza a MAYÚSCULAS en save().
    # Visible en la mayoría de templates: listados, mapa, popup, reportes.
    nombre_bote = models.CharField(max_length=50)

    # Dimensiones físicas de la embarcación en metros.
    # Validadas en clean() para ser estrictamente positivas.
    # Usadas para determinar compatibilidad con el espacio del muelle.
    eslora = models.DecimalField(max_digits=6, decimal_places=2)  # Longitud total
    manga  = models.DecimalField(max_digits=6, decimal_places=2)  # Anchura máxima
    calado = models.DecimalField(max_digits=6, decimal_places=2)  # Profundidad bajo el agua

    class Meta:
        db_table            = 'embarcacion'
        verbose_name        = 'Embarcación'
        verbose_name_plural = 'Embarcaciones'
        ordering            = ['nombre_bote']  # Alfabético en listados y dropdowns

    def save(self, *args, **kwargs):
        """Normaliza nombre_bote a MAYÚSCULAS antes de guardar."""
        if self.nombre_bote:
            self.nombre_bote = self.nombre_bote.upper()
        super().save(*args, **kwargs)

    def clean(self):
        """Valida que las dimensiones físicas sean valores positivos.
        Ejecutado por Django en full_clean() y desde el panel admin.
        Una embarcación con medidas en cero o negativas no tiene sentido físico."""
        if self.eslora  is not None and self.eslora  <= 0:
            raise ValidationError('La eslora debe ser mayor a 0.')
        if self.manga   is not None and self.manga   <= 0:
            raise ValidationError('La manga debe ser mayor a 0.')
        if self.calado  is not None and self.calado  <= 0:
            raise ValidationError('El calado debe ser mayor a 0.')

    def __str__(self):
        # Representación usada en admin, dropdowns de solicitud y relaciones __str__
        return self.nombre_bote