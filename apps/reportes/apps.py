from django import forms

class ReporteFiltroForm(forms.Form):
    ESTADO_CHOICES = (
        ('todos', 'Aceptados y Rechazados'),
        ('aceptado', 'Aceptados'),
        ('rechazado', 'Rechazados'),
    )

    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        label='Filtrar por estado',
        initial='todos'
    )