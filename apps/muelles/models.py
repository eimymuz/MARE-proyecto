# =============================================================================
# models.py — App: muelles
# Define los cuatro modelos que representan la infraestructura física de la
# marina: Muelle, Espacio, ZonaTierra y EtiquetaMuelle.
# Estos modelos son la base del mapa interactivo y del sistema de asignaciones.
#
# Modelos exportados:
#   - Muelle         → usado en: apps/asignaciones/models.py (FK en Asignacion),
#                                apps/mapa/views.py (filtro de muelles activos),
#                                apps/solicitudes/views.py (contexto de formulario),
#                                admin.py (esta app),
#                                templates/solicitudes/solicitud_list.html,
#                                templates/mapa/mapa_component.html
#
#   - Espacio        → usado en: apps/asignaciones/models.py (ManyToMany en Asignacion.espacios),
#                                apps/mapa/views.py (disponibilidad_json, asignar_espacio, inicio),
#                                apps/asistente/views.py (conteo de ocupación),
#                                views.py (esta app),
#                                templates/mapa/mapa_component.html (canvas del mapa)
#
#   - ZonaTierra     → usado en: apps/mapa/views.py (disponibilidad_json),
#                                views.py (esta app),
#                                templates/mapa/mapa_component.html (polígonos de tierra)
#
#   - EtiquetaMuelle → usado en: apps/mapa/views.py (disponibilidad_json),
#                                views.py (esta app),
#                                templates/mapa/mapa_component.html (labels del mapa)
# =============================================================================

from django.db import models
from django.core.exceptions import ValidationError


# -----------------------------------------------------------------------------
# Modelo: Muelle
# Representa una estructura física de atraque dentro de la marina.
# Cada muelle agrupa espacios (amarres) y puede activarse o desactivarse.
# El campo estado=False impide nuevas asignaciones (validado en Asignacion.clean()).
#
# Relaciones inversas:
#   muelle.espacios.all()      → todos los Espacio de este muelle
#   muelle.asignaciones.all()  → todas las Asignacion de este muelle
#   muelle.etiqueta            → EtiquetaMuelle (OneToOne, puede no existir)
# -----------------------------------------------------------------------------
class Muelle(models.Model):
    # Nombre identificador del muelle. Mostrado en listados, dropdowns y el mapa.
    nombre = models.CharField(max_length=120)

    # Tamaño máximo de embarcación admitida (en metros). Validado en clean().
    tam_maximo = models.DecimalField(max_digits=6, decimal_places=2)

    # Conteo informativo de espacios para referencia visual en el mapa SVG.
    # No se actualiza automáticamente; se gestiona desde el admin.
    total_espacios = models.PositiveIntegerField(default=0)  # ← para el mapa SVG

    # Si False, bloquea nuevas asignaciones (Asignacion.clean() lo verifica).
    # Usado en mapa_view para filtrar solo muelles activos en el dropdown.
    estado = models.BooleanField(default=True)

    # Coordenadas geográficas del muelle (lat/lon). Almacenadas pero actualmente
    # mostradas como readonly en el admin; no se usan en el mapa canvas.
    coordenada_x = models.DecimalField(max_digits=10, decimal_places=6)
    coordenada_y = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        db_table            = 'muelle'
        verbose_name        = 'Muelle'
        verbose_name_plural = 'Muelles'
        ordering            = ['nombre']

    def clean(self):
        """Valida restricciones físicas básicas del muelle.
        Ejecutado desde el admin y en full_clean()."""
        if self.tam_maximo is not None and self.tam_maximo <= 0:
            raise ValidationError('El tamaño máximo debe ser mayor a 0.')
        if self.total_espacios is not None and self.total_espacios < 1:
            raise ValidationError('El muelle debe tener al menos 1 espacio.')

    def __str__(self):
        return self.nombre


# -----------------------------------------------------------------------------
# Modelo: Espacio
# Representa un amarre individual dentro de un muelle, dibujado como un
# rectángulo en el canvas del mapa. Tiene posición, tamaño y rotación para
# el renderizado SVG.
#
# Tipos de espacio:
#   es_pasillo=False → amarre asignable; debe tener número único dentro del muelle
#   es_pasillo=True  → elemento visual de separación; no es asignable, sin número
#
# La restricción UniqueConstraint garantiza que no haya dos amarres con el
# mismo número en el mismo muelle (los pasillos quedan excluidos).
#
# Coordenadas (pos_x, pos_y, ancho, alto) están en píxeles del canvas.
# En mapa/views.py se dividen /10 para convertirlas a metros al comparar
# con la eslora y manga de la embarcación.
#
# Relaciones inversas:
#   espacio.asignaciones.all() → todas las Asignacion que incluyen este espacio
# -----------------------------------------------------------------------------
class Espacio(models.Model):
    # FK al muelle contenedor. CASCADE: si se borra el muelle, se borran sus espacios.
    # related_name='espacios' permite: muelle.espacios.all()
    muelle = models.ForeignKey(
        Muelle,
        on_delete=models.CASCADE,       # si se borra el muelle, se borran sus espacios
        related_name='espacios'
    )

    # Número de amarre visible en el mapa (ej: "5", "12"). Nulo solo para pasillos.
    # La restricción uq_espacio_muelle_numero garantiza unicidad por muelle.
    numero = models.PositiveIntegerField(null=True, blank=True)

    # Posición del rectángulo en el canvas SVG (píxeles)
    pos_x = models.DecimalField(max_digits=8, decimal_places=2)  # coord X en el canvas SVG
    pos_y = models.DecimalField(max_digits=8, decimal_places=2)  # coord Y en el canvas SVG

    # Dimensiones del rectángulo en el canvas SVG (píxeles).
    # ancho/10 → ancho real en metros (manga), alto/10 → largo real en metros (eslora).
    ancho = models.DecimalField(max_digits=6, decimal_places=2)  # width del rectángulo
    alto  = models.DecimalField(max_digits=6, decimal_places=2)  # height del rectángulo

    # Rotación en grados del rectángulo en el canvas (0, 90, 180 o 270).
    # Afecta el cálculo de dimensiones combinadas en mapa/views.py (grupos contiguos).
    rotacion = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # True → es un pasillo visual entre amarres, no asignable ni contabilizado
    # como espacio disponible. Excluido de conteos en mapa/views.py e inicio.
    es_pasillo = models.BooleanField(default=False)

    # Permite desactivar un espacio sin eliminarlo (no aparece como disponible).
    activo = models.BooleanField(default=True)

    class Meta:
        db_table            = 'espacio'
        verbose_name        = 'Espacio'
        verbose_name_plural = 'Espacios'
        ordering            = ['muelle', 'numero']
        # No puede haber dos espacios con el mismo número en el mismo muelle.
        # La condición excluye pasillos (es_pasillo=False) ya que no tienen número.
        constraints = [
            models.UniqueConstraint(
                fields=['muelle', 'numero'],
                condition=models.Q(es_pasillo=False),
                name='uq_espacio_muelle_numero'
            )
        ]

    def clean(self):
        """Valida que los espacios asignables tengan número y que las
        dimensiones sean positivas. Ejecutado desde el admin y full_clean()."""
        if not self.es_pasillo and self.numero is None:
            raise ValidationError('Los espacios asignables deben tener número.')
        if self.ancho is not None and self.ancho <= 0:
            raise ValidationError('El ancho debe ser mayor a 0.')
        if self.alto is not None and self.alto <= 0:
            raise ValidationError('El alto debe ser mayor a 0.')

    def __str__(self):
        # Usado en el admin y en mensajes de error de asignación
        return f'{self.muelle.nombre} — Espacio {self.numero}'


# -----------------------------------------------------------------------------
# Modelo: ZonaTierra
# Representa polígonos de tierra firme o zonas decorativas dibujadas sobre
# el canvas del mapa para dar contexto visual a la marina.
#
# El campo 'puntos' almacena un JSON con la lista de vértices del polígono:
#   [{"x": 10, "y": 20}, {"x": 50, "y": 20}, ...]
# Este JSON es parseado en el JS de mapa_component.html para dibujar el path.
#
# Usado en: apps/mapa/views.py (disponibilidad_json y zonas_tierra_json),
#           templates/mapa/mapa_component.html (canvas del mapa)
# -----------------------------------------------------------------------------
class ZonaTierra(models.Model):
    puntos = models.TextField()        # JSON: [{"x":10,"y":20}, ...]
    color  = models.CharField(max_length=7, default='#7ab648')  # Color hex del relleno del polígono
    nombre = models.CharField(max_length=80, blank=True, default='')  # Etiqueta opcional para el admin

    class Meta:
        db_table            = 'zona_tierra'
        verbose_name        = 'Zona de tierra'
        verbose_name_plural = 'Zonas de tierra'

    def __str__(self):
        return self.nombre or f'Zona #{self.pk}'


# -----------------------------------------------------------------------------
# Modelo: EtiquetaMuelle
# Etiqueta de texto personalizable que se superpone sobre el canvas del mapa
# para identificar visualmente cada muelle. Es OneToOne con Muelle: cada
# muelle tiene como máximo una etiqueta.
#
# pos_x, pos_y → posición en píxeles del canvas
# texto        → por defecto el nombre del muelle, editable desde el admin
# tamanio      → font-size en píxeles para el canvas
# color        → color hex del texto (contraste sobre el fondo del mapa)
#
# Relación inversa: muelle.etiqueta → la EtiquetaMuelle de ese muelle
# Usado en: apps/mapa/views.py (disponibilidad_json y etiquetas_json),
#           templates/mapa/mapa_component.html (renderiza el texto sobre el canvas)
# -----------------------------------------------------------------------------
class EtiquetaMuelle(models.Model):
    # OneToOne con CASCADE: si se borra el muelle, se borra su etiqueta.
    # related_name='etiqueta' permite acceder como: muelle.etiqueta
    muelle  = models.OneToOneField(
        Muelle, on_delete=models.CASCADE, related_name='etiqueta'
    )
    pos_x   = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Posición X en el canvas
    pos_y   = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Posición Y en el canvas
    texto   = models.CharField(max_length=80)         # por defecto = nombre del muelle
    tamanio = models.PositiveIntegerField(default=14)  # font-size en px para el canvas SVG
    color   = models.CharField(max_length=7, default='#ffffff')  # Color hex del texto

    class Meta:
        db_table = 'etiqueta_muelle'
        verbose_name = 'Etiqueta de muelle'
        verbose_name_plural = 'Etiquetas de muelles'

    def __str__(self):
        return f'Etiqueta — {self.muelle.nombre}'