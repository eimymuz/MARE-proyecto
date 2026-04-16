from django.contrib import admin
from django.urls import include, path
from apps.mapa import views as mapa_views

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Área pública (cliente)
    path('', include('apps.publico.urls')),

    # Dashboard admin
    path('inicio/', mapa_views.inicio, name='inicio'),

    # Apps
    path('solicitudes/',   include('apps.solicitudes.urls')),
    path('muelles/',       include('apps.muelles.urls')),
    path('mapa/',          include('apps.mapa.urls')),
    path('asignaciones/',  include('apps.asignaciones.urls')),
    path('clientes/',      include('apps.clientes.urls')),
    path('embarcaciones/', include('apps.embarcaciones.urls')),
]
