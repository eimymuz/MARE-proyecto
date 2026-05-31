# =============================================================================
# views.py — App: usuarios
# Gestión de autenticación y administración de usuarios del sistema MARE.
# Incluye login/logout y el CRUD completo de administradores, restringido
# exclusivamente a usuarios con rol de gerente mediante el decorador solo_gerente.
#
# Vistas:
#   login_view        GET/POST /login/                        → usuarios/login.html
#   logout_view       GET/POST /logout/                       → redirect a login
#   usuario_list      GET      /usuarios/                     → usuarios/usuario_list.html
#   usuario_crear     POST     /usuarios/crear/               → redirect a usuario_list
#   usuario_editar    POST     /usuarios/<pk>/editar/         → redirect a usuario_list
#   usuario_eliminar  POST     /usuarios/<pk>/eliminar/       → redirect a usuario_list
#   usuario_reactivar POST     /usuarios/<pk>/reactivar/      → redirect a usuario_list
#
# Decorador propio:
#   solo_gerente → restringe vistas a usuarios con Administrador.rol == 'gerente'
#
# Modelos usados:
#   django.contrib.auth.models.User   (autenticación nativa de Django)
#   apps.asignaciones.models.Administrador (perfil extendido del sistema)
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm  # Formulario estándar de login de Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from apps.asignaciones.models import Administrador  # Perfil de rol del usuario en el sistema


# =============================================================================
# Decorador: solo_gerente
# Wrapper que restringe el acceso a una vista únicamente a usuarios cuyo
# perfil Administrador tiene rol='gerente'.
# Si el usuario no tiene perfil Administrador (AttributeError al acceder a
# request.user.administrador) o no es gerente, redirige al inicio.
#
# Expone __wrapped__ para que @login_required y otros decoradores puedan
# acceder a la función original si es necesario (introspección, tests).
#
# Uso: @login_required + @solo_gerente en todas las vistas de gestión de usuarios.
# Consumido por: usuario_list, usuario_crear, usuario_editar,
#                usuario_eliminar, usuario_reactivar
# =============================================================================
def solo_gerente(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            # request.user.administrador accede al related_name definido en Administrador.user (OneToOne)
            if not request.user.administrador.es_gerente():
                messages.error(request, 'No tienes permisos para realizar esta acción.')
                return redirect('inicio')
        except:
            # Si el usuario no tiene perfil Administrador, redirige al inicio silenciosamente
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func  # Permite introspección de la función original
    return wrapper


# =============================================================================
# Vista: login_view
# Maneja la autenticación de usuarios del sistema.
# GET: muestra el formulario de login (usuarios/login.html).
# POST: valida credenciales con AuthenticationForm y authenticate().
#
# Restricción extra: además de autenticarse con Django, el usuario DEBE tener
# un perfil Administrador asociado (hasattr(user, 'administrador')).
# Esto impide que usuarios de Django sin perfil MARE accedan al sistema,
# aunque sus credenciales sean correctas.
#
# Consumido por:
#   - templates/usuarios/login.html  (formulario de login)
#   - Todas las vistas protegidas con @login_required redirigen aquí si no hay sesión
# =============================================================================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user     = authenticate(username=username, password=password)
            if user is not None:
                # Verifica que el usuario Django tenga perfil Administrador en el sistema MARE
                if hasattr(user, 'administrador'):
                    login(request, user)
                    return redirect('inicio')
                else:
                    messages.error(request, 'No tienes permisos para acceder al sistema.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})


# =============================================================================
# Vista: logout_view
# Cierra la sesión del usuario actual y redirige a la página de login.
# No requiere autenticación previa para evitar errores si la sesión ya expiró.
# =============================================================================
def logout_view(request):
    logout(request)
    return redirect('login')


# =============================================================================
# Vista: usuario_list
# Lista todos los administradores del sistema (activos e inactivos).
# Solo accesible para gerentes (@solo_gerente).
# Envía el queryset a usuario_list.html para renderizar la tabla con botones
# de acción (editar, desactivar, reactivar).
#
# Consumido por:
#   - templates/usuarios/usuario_list.html
#   - templates/components/navbar.html  (enlace "Usuarios", visible solo para gerentes)
# =============================================================================
@login_required
@solo_gerente
def usuario_list(request):
    # select_related('user') evita N+1 al acceder a user.first_name, email, etc. en el template
    administradores = Administrador.objects.select_related('user').order_by('user__first_name')
    return render(request, 'usuarios/usuario_list.html', {'administradores': administradores})


# =============================================================================
# Vista: usuario_crear
# POST: crea un nuevo User de Django y su perfil Administrador asociado.
# Solo accesible para gerentes. No tiene vista GET propia: el formulario de
# creación está en el modal de usuario_list.html.
#
# Lógica de permisos del sistema:
#   - rol='gerente' → is_staff=True, is_superuser=True (acceso al admin de Django)
#   - rol='empleado' → is_staff=False, is_superuser=False
#
# Verifica duplicados de username antes de crear para dar un mensaje amigable
# (create_user lanzaría IntegrityError sin el mensaje claro).
#
# Consumido por:
#   - templates/usuarios/usuario_list.html  (modal de creación → POST a usuario_crear)
# =============================================================================
@login_required
@solo_gerente
def usuario_crear(request):
    if request.method == 'POST':
        username   = request.POST.get('username')
        password   = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        rol        = request.POST.get('rol', 'empleado')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya existe.')
            return redirect('usuario_list')

        # create_user hashea la contraseña automáticamente (no almacena texto plano)
        user = User.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name, email=email
        )
        # Los gerentes reciben acceso al admin de Django; los empleados no
        user.is_staff      = rol == 'gerente'
        user.is_superuser  = rol == 'gerente'
        user.save()
        # Crea el perfil Administrador vinculado al User recién creado
        Administrador.objects.create(user=user, rol=rol)
        messages.success(request, f'Usuario {first_name} {last_name} creado correctamente.')

    return redirect('usuario_list')


# =============================================================================
# Vista: usuario_editar
# POST: edita los datos de un Administrador existente y su User asociado.
# Solo accesible para gerentes. El formulario está en usuario_list.html.
#
# Protección: un gerente no puede cambiar su propio rol para evitar que
# se quite permisos accidentalmente y quede sin acceso.
# Si se envía una nueva contraseña, se usa set_password() para hashearla
# correctamente (no almacena texto plano).
# Sincroniza is_staff/is_superuser con el rol para mantener consistencia
# entre el sistema MARE y el admin de Django.
#
# Consumido por:
#   - templates/usuarios/usuario_list.html  (modal de edición → POST a usuario_editar)
# =============================================================================
@login_required
@solo_gerente
def usuario_editar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    if request.method == 'POST':
        admin.user.first_name = request.POST.get('first_name')
        admin.user.last_name  = request.POST.get('last_name')
        admin.user.email      = request.POST.get('email')

        # Protección: el gerente no puede cambiar su propio rol
        if admin.user != request.user:
            admin.rol = request.POST.get('rol', 'empleado')

        nueva_pass = request.POST.get('password')
        if nueva_pass:
            admin.user.set_password(nueva_pass)  # Hashea la contraseña antes de guardar

        # Sincroniza los permisos de Django con el rol del sistema MARE
        admin.user.is_staff      = admin.rol == 'gerente'
        admin.user.is_superuser  = admin.rol == 'gerente'
        admin.user.save()
        admin.save()  # Administrador.save() también normaliza nombre/email a mayúsculas/minúsculas
        messages.success(request, 'Usuario actualizado correctamente.')

    return redirect('usuario_list')


# =============================================================================
# Vista: usuario_eliminar
# POST: desactiva un administrador (soft-delete lógico).
# No borra el registro de la BD; marca activo=False en Administrador y
# is_active=False en User para que no pueda iniciar sesión.
#
# Protección: un gerente no puede desactivarse a sí mismo.
# La desactivación es reversible mediante usuario_reactivar.
#
# Consumido por:
#   - templates/usuarios/usuario_list.html  (botón "Desactivar" → POST a usuario_eliminar)
# =============================================================================
@login_required
@solo_gerente
def usuario_eliminar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    if admin.user == request.user:
        messages.error(request, 'No puedes desactivarte a ti mismo.')
        return redirect('usuario_list')
    # Soft-delete: desactiva en ambas capas (MARE y Django Auth)
    admin.activo         = False   # Administrador.activo → usado en navbar y lógica del sistema
    admin.user.is_active = False   # User.is_active → Django rechaza el login automáticamente
    admin.user.save()
    admin.save()
    nombre = admin.user.get_full_name() or admin.user.username
    messages.success(request, f'Usuario {nombre} desactivado correctamente.')
    return redirect('usuario_list')


# =============================================================================
# Vista: usuario_reactivar
# POST: reactiva un administrador previamente desactivado.
# Revierte el soft-delete de usuario_eliminar: activo=True y is_active=True.
# El usuario recupera acceso al sistema al iniciar sesión.
#
# Consumido por:
#   - templates/usuarios/usuario_list.html  (botón "Reactivar" → POST a usuario_reactivar)
# =============================================================================
@login_required
@solo_gerente
def usuario_reactivar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    admin.activo         = True   # Reactiva en MARE
    admin.user.is_active = True   # Reactiva en Django Auth para permitir login
    admin.user.save()
    admin.save()
    nombre = admin.user.get_full_name() or admin.user.username
    messages.success(request, f'Usuario {nombre} reactivado correctamente.')
    return redirect('usuario_list')