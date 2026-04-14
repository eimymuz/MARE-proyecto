from django.db import models

class Cliente(models.Model):
    fullname = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)

    class Meta:
        db_table            = 'clientes'          # ← nombre limpio en BD

        verbose_name        = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering            = ['fullname']

    def __str__(self):
        return self.fullname
