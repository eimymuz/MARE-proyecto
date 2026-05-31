# =============================================================================
# urls.py — App: asistente
# Registra el endpoint del chatbot Coral.
# Incluido en config/urls.py bajo el prefijo /asistente/.
#
# Ruta resultante:
#   POST /asistente/  → views.asistente  (name='asistente')
#
# Consumido por:
#   - templates/components/coral.html  (hace fetch POST a {% url 'asistente' %})
# =============================================================================

from django.urls import path
from . import views  # Importa views.py de esta misma app

urlpatterns = [
    # Endpoint único del asistente. Solo acepta POST (enforce en la vista con @require_POST).
    path('', views.asistente, name='asistente'),
]