# =============================================================================
# urls.py — App: usuarios
# Define las rutas de autenticación y gestión de usuarios del sistema MARE.
# Incluido en config/urls.py directamente en la raíz (sin prefijo propio).
#
# Rutas resultantes:
#   GET/POST /login/                         → views.login_view        (name='login')
#   GET/POST /logout/                        → views.logout_view       (name='logout')
#   GET      /usuarios/                      → views.usuario_list      (name='usuario_list')
#   POST     /usuarios/crear/               → views.usuario_crear     (name='usuario_crear')
#   POST     /usuarios/<pk>/editar/         → views.usuario_editar    (name='usuario_editar')
#   POST     /usuarios/<pk>/eliminar/       → views.usuario_eliminar  (name='usuario_eliminar')
#   POST     /usuarios/<pk>/reactivar/      → views.usuario_reactivar (name='usuario_reactivar')
#
# Las rutas de gestión (/usuarios/*) requieren @login_required + @solo_gerente.
# Las rutas de auth (/login/, /logout/) son públicas.
#
# Consumidores:
#   - templates/usuarios/login.html          (formulario de autenticación)
#   - templates/usuarios/usuario_list.html   (tabla CRUD de administradores)
#   - templates/components/navbar.html       (enlace "Usuarios" solo para gerentes,
#                                             enlace "Cerrar sesión" → logout)
# =============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # Autenticación (públicas)
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Gestión de usuarios (solo gerente)
    path('usuarios/',                          views.usuario_list,     name='usuario_list'),
    path('usuarios/crear/',                    views.usuario_crear,    name='usuario_crear'),
    path('usuarios/<int:pk>/editar/',          views.usuario_editar,   name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/',        views.usuario_eliminar, name='usuario_eliminar'),
    path('usuarios/<int:pk>/reactivar/',       views.usuario_reactivar, name='usuario_reactivar'),
]