from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/',        views.usuario_list,     name='usuario_list'),
    path('usuarios/crear/',  views.usuario_crear,    name='usuario_crear'),
    path('usuarios/<int:pk>/editar/',   views.usuario_editar,   name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
    path('usuarios/<int:pk>/reactivar/', views.usuario_reactivar, name='usuario_reactivar'),
]