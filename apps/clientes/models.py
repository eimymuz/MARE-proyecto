# =============================================================================
# models.py — App: clientes
# Define el modelo Cliente, que representa a los dueños de embarcaciones
# que solicitan estadía en la marina.
#
# Modelo exportado:
#   - Cliente → usado en:
#       apps/embarcaciones/models.py  (FK: Embarcacion.cliente)
#       apps/publico/views.py         (creación de cliente desde el formulario público)
#       admin.py (esta app)
#       templates/components/popup_solicitud.html  (muestra nombre del cliente)
#       templates/mapa/mapa_component.html         (nombre del cliente en el mapa)
#       templates/solicitudes/solicitud_list.html  (columna cliente en el listado)
#       templates/solicitudes/solicitud_aprobadas.html
#       templates/reporte/reporte.html / reporte_pdf.html
# =============================================================================

from django.db import models


# -----------------------------------------------------------------------------
# Modelo: Cliente
# Persona natural o jurídica que posee embarcaciones registradas en el sistema.
# Se crea al momento de enviar la primera solicitud desde la vista pública
# (apps/publico/views.py). No tiene usuario Django asociado (no inicia sesión).
#
# Relación inversa clave:
#   cliente.embarcaciones.all()  →  todas las Embarcaciones de este cliente
#   (definida por related_name en apps/embarcaciones/models.py)
# -----------------------------------------------------------------------------
class Cliente(models.Model):
    # Nombre completo del cliente. Se normaliza a MAYÚSCULAS en save().
    # Visible en: solicitud_list.html, popup_solicitud.html, mapa_component.html, reportes.
    fullname = models.CharField(max_length=120)

    # Email único por cliente; se usa como identificador en el formulario público
    # para reutilizar un cliente existente en lugar de duplicarlo.
    # Se normaliza a minúsculas en save(). Usado en: apps/publico/views.py.
    email = models.EmailField(unique=True)

    # Número de teléfono de contacto. Visible en el panel admin (ClienteAdmin).
    telefono = models.CharField(max_length=15)

    class Meta:
        db_table            = 'clientes'          # ← nombre limpio en BD
        verbose_name        = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering            = ['fullname']        # Listados ordenados alfabéticamente

    def save(self, *args, **kwargs):
        """Normaliza los datos antes de guardar:
        - fullname → MAYÚSCULAS (convención del sistema para nombres)
        - email    → minúsculas (convención estándar para emails)
        Garantiza consistencia al buscar/comparar en publico/views.py."""
        if self.fullname:
            self.fullname = self.fullname.upper()
        if self.email:
            self.email = self.email.lower()  # email siempre minúsculas
        super().save(*args, **kwargs)

    def __str__(self):
        # Representación usada en el panel admin, dropdowns y relaciones __str__
        return self.fullname
    
