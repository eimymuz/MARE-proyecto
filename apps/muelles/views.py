# =============================================================================
# views.py — App: muelles
# APIs de solo lectura que sirven los datos de infraestructura de la marina
# (espacios, zonas de tierra y etiquetas) al canvas del mapa interactivo.
# Todas requieren sesión autenticada y retornan JSON.
#
# Rutas (definidas en urls.py de esta app):
#   GET /muelles/<pk>/espacios/json/ → muelle_espacios_json  (name='muelle_espacios_json')
#   GET /muelles/zonas/json/         → zonas_tierra_json     (name='zonas_tierra_json')
#   GET /muelles/etiquetas/json/     → etiquetas_json        (name='etiquetas_json')
#
# Consumido por:
#   - templates/mapa/mapa_component.html  (fetch JS para construir el canvas del mapa)
# =============================================================================

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Muelle, Espacio, ZonaTierra, EtiquetaMuelle  # Modelos de esta misma app


# -----------------------------------------------------------------------------
# Vista: muelle_espacios_json
# Devuelve el nombre del muelle y la lista completa de sus espacios (incluidos
# pasillos) con todos los campos necesarios para dibujarlos en el canvas.
# Usado por mapa_component.html cuando el usuario cambia el muelle activo
# en el selector del mapa.
#
# Parámetro de URL: pk (int) → ID del Muelle
# Respuesta JSON:
#   muelle   → {id, nombre}
#   espacios → [{id, numero, pos_x, pos_y, ancho, alto, rotacion, es_pasillo, activo}, ...]
# -----------------------------------------------------------------------------
@login_required
def muelle_espacios_json(request, pk):
    muelle   = get_object_or_404(Muelle, pk=pk)  # 404 si el muelle no existe
    espacios = list(
        # .values() serializa directamente a dict evitando instanciar objetos Python
        muelle.espacios.values(
            'id', 'numero', 'pos_x', 'pos_y',
            'ancho', 'alto', 'rotacion', 'es_pasillo', 'activo',
        )
    )
    return JsonResponse({
        'muelle':   {'id': muelle.pk, 'nombre': muelle.nombre},
        'espacios': espacios,
    })


# -----------------------------------------------------------------------------
# Vista: zonas_tierra_json
# Devuelve todas las ZonaTierra registradas con sus puntos, color y nombre.
# El JS de mapa_component.html parsea el campo 'puntos' (JSON string) y
# dibuja cada polígono sobre el canvas del mapa como zona de tierra firme.
#
# Respuesta JSON:
#   zonas → [{id, nombre, puntos (JSON string), color}, ...]
# -----------------------------------------------------------------------------
@login_required
def zonas_tierra_json(request):
    zonas = list(ZonaTierra.objects.values('id', 'nombre', 'puntos', 'color'))
    return JsonResponse({'zonas': zonas})


# -----------------------------------------------------------------------------
# Vista: etiquetas_json
# Devuelve todas las EtiquetaMuelle con su posición, texto, tamaño y color
# para que el JS de mapa_component.html las renderice como labels sobre el canvas.
# select_related('muelle') no es estrictamente necesario aquí porque .values()
# no accede al objeto Muelle completo, pero se mantiene por legibilidad.
#
# Respuesta JSON:
#   etiquetas → [{id, muelle_id, pos_x, pos_y, texto, tamanio, color}, ...]
# -----------------------------------------------------------------------------
@login_required
def etiquetas_json(request):
    etiquetas = list(
        EtiquetaMuelle.objects.select_related('muelle').values(
            'id', 'muelle_id', 'pos_x', 'pos_y', 'texto', 'tamanio', 'color'
        )
    )
    return JsonResponse({'etiquetas': etiquetas})