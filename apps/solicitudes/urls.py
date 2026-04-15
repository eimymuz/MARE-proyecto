from django.urls import path
from . import views

urlpatterns = [
    # CRUDs por estado
    path('',                          views.solicitud_list,            name='solicitud_list'),
    path('en-espera/',                views.solicitud_en_espera_list,  name='solicitud_en_espera_list'),
    path('aprobadas/',                views.solicitud_aprobadas_list,  name='solicitud_aprobadas_list'),

    # CRUD general
    path('<int:pk>/',                 views.solicitud_detail,          name='solicitud_detail'),
    path('<int:pk>/editar/',          views.solicitud_update,          name='solicitud_update'),
    path('<int:pk>/eliminar/',        views.solicitud_delete,          name='solicitud_delete'),
    path('<int:pk>/estado/<str:nuevo_estado>/', views.solicitud_cambiar_estado, name='solicitud_cambiar_estado'),
    path('<int:pk>/json/', views.solicitud_detalle_json, name='solicitud_detalle_json'),
]