from django.db import models
from django.core.exceptions import ValidationError
from apps.clientes.models import Cliente


class TipoBarco(models.Model):
    tipo_barco = models.CharField(max_length=80)

    class Meta:
        db_table            = 'tipo_barco'

        verbose_name        = 'Tipo de barco'
        verbose_name_plural = 'Tipos de barco'
        ordering            = ['tipo_barco']
        
    def save(self, *args, **kwargs):
        if self.tipo_barco:
            self.tipo_barco = self.tipo_barco.upper()
        super().save(*args, **kwargs)


    def __str__(self):
        return self.tipo_barco


class Embarcacion(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )
    tipo_barco = models.ForeignKey(
        TipoBarco,
        on_delete=models.PROTECT,
        related_name="embarcaciones"
    )
    nombre_bote = models.CharField(max_length=50)
    eslora = models.DecimalField(max_digits=6, decimal_places=2)
    manga = models.DecimalField(max_digits=6, decimal_places=2)
    calado = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table            = 'embarcacion'

        verbose_name        = 'Embarcación'
        verbose_name_plural = 'Embarcaciones'
        ordering            = ['nombre_bote']

    def save(self, *args, **kwargs):
        if self.nombre_bote:
            self.nombre_bote = self.nombre_bote.upper()
        super().save(*args, **kwargs)

    def clean(self):
        if self.eslora  is not None and self.eslora  <= 0:
            raise ValidationError('La eslora debe ser mayor a 0.')
        if self.manga   is not None and self.manga   <= 0:
            raise ValidationError('La manga debe ser mayor a 0.')
        if self.calado  is not None and self.calado  <= 0:
            raise ValidationError('El calado debe ser mayor a 0.')

    def __str__(self):
        return self.nombre_bote