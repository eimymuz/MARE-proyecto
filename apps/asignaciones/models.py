from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.solicitudes.models import Solicitud
from apps.muelles.models import Muelle, Espacio


class Administrador(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='administrador'
    )

    class Meta:
        db_table            = 'administrador'
        verbose_name        = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Asignacion(models.Model):
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="asignaciones"
    )
    muelle = models.ForeignKey(
        Muelle,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.PROTECT,
        related_name="asignaciones"
    )
    
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    # Una asignación puede ocupar uno o varios espacios simultáneamente
    espacios = models.ManyToManyField(
        Espacio,
        related_name='asignaciones',
        blank=False,
    )
    
    activa = models.BooleanField(default=True)


    class Meta:
        db_table = 'asignacion'
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"
        ordering            = ['-fecha_inicio']

    def clean(self):
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha fin debe ser posterior a la fecha inicio.")

        if self.muelle_id and not self.muelle.estado:
            raise ValidationError("No se puede asignar: el muelle está inactivo.")

        if self.solicitud_id:
            if self.fecha_inicio and self.fecha_inicio < self.solicitud.fecha_llegada:
                raise ValidationError("La fecha de inicio no puede ser anterior a la llegada de la solicitud.")

            if self.fecha_fin and self.fecha_fin > self.solicitud.fecha_salida:
                raise ValidationError("La fecha fin no puede ser posterior a la salida de la solicitud.")
        
    def validar_traslape_espacios(self):
        espacios_ids = self.espacios.values_list('id', flat=True)
        traslapes = Asignacion.objects.filter(
            espacios__in=espacios_ids,
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio,
        ).exclude(pk=self.pk).distinct()

        if traslapes.exists():
            raise ValidationError(
                'Uno o más espacios ya están ocupados en esas fechas.'
            )


    def __str__(self):
        return f'Asignacion #{self.pk}'