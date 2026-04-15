from django.db import models
from django.core.exceptions import ValidationError


class Muelle(models.Model):
    nombre = models.CharField(max_length=120)
    tam_maximo = models.DecimalField(max_digits=6, decimal_places=2)
    total_espacios = models.PositiveIntegerField(default=0)  # ← para el mapa SVG


    estado = models.BooleanField(default=True)
    coordenada_x = models.DecimalField(max_digits=10, decimal_places=6)
    coordenada_y = models.DecimalField(max_digits=10, decimal_places=6)


    class Meta:
        db_table            = 'muelle'

        verbose_name        = 'Muelle'
        verbose_name_plural = 'Muelles'
        ordering            = ['nombre']


    def clean(self):
        if self.tam_maximo is not None and self.tam_maximo <= 0:
            raise ValidationError('El tamaño máximo debe ser mayor a 0.')
        if self.total_espacios is not None and self.total_espacios < 1:
            raise ValidationError('El muelle debe tener al menos 1 espacio.')

    def __str__(self):
        return self.nombre


class Espacio(models.Model):
    muelle     = models.ForeignKey(
        Muelle,
        on_delete=models.CASCADE,       # si se borra el muelle, se borran sus espacios
        related_name='espacios'
    )
    numero = models.PositiveIntegerField(null=True, blank=True)
    pos_x      = models.DecimalField(max_digits=8, decimal_places=2)  # coord X en el canvas SVG
    pos_y      = models.DecimalField(max_digits=8, decimal_places=2)  # coord Y en el canvas SVG
    ancho      = models.DecimalField(max_digits=6, decimal_places=2)  # width del rectángulo
    alto       = models.DecimalField(max_digits=6, decimal_places=2)  # height del rectángulo
    rotacion   = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # ← agregar
    es_pasillo = models.BooleanField(default=False)                   # pasillo visual, no asignable
    activo     = models.BooleanField(default=True)

    class Meta:
        db_table            = 'espacio'
        verbose_name        = 'Espacio'
        verbose_name_plural = 'Espacios'
        ordering            = ['muelle', 'numero']
        # No puede haber dos espacios con el mismo número en el mismo muelle
        constraints = [
            models.UniqueConstraint(
                fields=['muelle', 'numero'],
                condition=models.Q(es_pasillo=False),
                name='uq_espacio_muelle_numero'
            )
        ]

    def clean(self):
        if not self.es_pasillo and self.numero is None:
            raise ValidationError('Los espacios asignables deben tener número.')
        if self.ancho is not None and self.ancho <= 0:
            raise ValidationError('El ancho debe ser mayor a 0.')
        if self.alto is not None and self.alto <= 0:
            raise ValidationError('El alto debe ser mayor a 0.')

    def __str__(self):
        return f'{self.muelle.nombre} — Espacio {self.numero}'
    
class ZonaTierra(models.Model):
    puntos = models.TextField()        # JSON: [{"x":10,"y":20}, ...]
    color  = models.CharField(max_length=7, default='#7ab648')
    nombre = models.CharField(max_length=80, blank=True, default='')

    class Meta:
        db_table            = 'zona_tierra'
        verbose_name        = 'Zona de tierra'
        verbose_name_plural = 'Zonas de tierra'

    def __str__(self):
        return self.nombre or f'Zona #{self.pk}'
    
class EtiquetaMuelle(models.Model):
    muelle  = models.OneToOneField(
        Muelle, on_delete=models.CASCADE, related_name='etiqueta'
    )
    pos_x   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    pos_y   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    texto   = models.CharField(max_length=80)        # por defecto = nombre del muelle
    tamanio = models.PositiveIntegerField(default=14) # font-size en px
    color   = models.CharField(max_length=7, default='#ffffff')

    class Meta:
        db_table = 'etiqueta_muelle'
        verbose_name = 'Etiqueta de muelle'
        verbose_name_plural = 'Etiquetas de muelles'

    def __str__(self):
        return f'Etiqueta — {self.muelle.nombre}'