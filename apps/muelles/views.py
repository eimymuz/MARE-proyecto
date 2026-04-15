from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Muelle, Espacio, ZonaTierra, EtiquetaMuelle


@login_required
def muelle_espacios_json(request, pk):
    muelle   = get_object_or_404(Muelle, pk=pk)
    espacios = list(
        muelle.espacios.values(
            'id', 'numero', 'pos_x', 'pos_y',
            'ancho', 'alto', 'rotacion', 'es_pasillo', 'activo',
        )
    )
    return JsonResponse({
        'muelle':   {'id': muelle.pk, 'nombre': muelle.nombre},
        'espacios': espacios,
    })


@login_required
def zonas_tierra_json(request):
    zonas = list(ZonaTierra.objects.values('id', 'nombre', 'puntos', 'color'))
    return JsonResponse({'zonas': zonas})


@login_required
def etiquetas_json(request):
    etiquetas = list(
        EtiquetaMuelle.objects.select_related('muelle').values(
            'id', 'muelle_id', 'pos_x', 'pos_y', 'texto', 'tamanio', 'color'
        )
    )
    return JsonResponse({'etiquetas': etiquetas})