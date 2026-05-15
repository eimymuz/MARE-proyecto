from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from apps.asignaciones.models import Administrador


# ── Decorator para vistas solo de gerente ──
def solo_gerente(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            if not request.user.administrador.es_gerente():
                messages.error(request, 'No tienes permisos para realizar esta acción.')
                return redirect('inicio')
        except:
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    wrapper.__wrapped__ = view_func
    return wrapper


# ── Login con verificación de administrador ──
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
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


# ── Logout ──
def logout_view(request):
    logout(request)
    return redirect('login')


# ── Lista de usuarios (solo gerente) ──
@login_required
@solo_gerente
def usuario_list(request):
    administradores = Administrador.objects.select_related('user').order_by('user__first_name')
    return render(request, 'usuarios/usuario_list.html', {'administradores': administradores})


# ── Crear usuario (solo gerente) ──
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

        user = User.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name, email=email
        )
        user.is_staff = rol == 'gerente'
        user.is_superuser = rol == 'gerente'
        user.save()
        Administrador.objects.create(user=user, rol=rol)
        messages.success(request, f'Usuario {first_name} {last_name} creado correctamente.')

    return redirect('usuario_list')


# ── Editar usuario (solo gerente) ──
@login_required
@solo_gerente
def usuario_editar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    if request.method == 'POST':
        admin.user.first_name = request.POST.get('first_name')
        admin.user.last_name  = request.POST.get('last_name')
        admin.user.email      = request.POST.get('email')

        # No permitir que el gerente se cambie su propio rol
        if admin.user != request.user:
            admin.rol = request.POST.get('rol', 'empleado')

        nueva_pass = request.POST.get('password')
        if nueva_pass:
            admin.user.set_password(nueva_pass)
            
        admin.user.is_staff = admin.rol == 'gerente'
        admin.user.is_superuser = admin.rol == 'gerente'
        admin.user.save()
        admin.save()
        messages.success(request, 'Usuario actualizado correctamente.')

    return redirect('usuario_list')


# ── Eliminar usuario (solo gerente) ──
@login_required
@solo_gerente
def usuario_eliminar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    if admin.user == request.user:
        messages.error(request, 'No puedes desactivarte a ti mismo.')
        return redirect('usuario_list')
    admin.activo = False
    admin.user.is_active = False
    admin.user.save()
    admin.save()
    nombre = admin.user.get_full_name() or admin.user.username
    messages.success(request, f'Usuario {nombre} desactivado correctamente.')
    return redirect('usuario_list')


@login_required
@solo_gerente
def usuario_reactivar(request, pk):
    admin = Administrador.objects.select_related('user').get(pk=pk)
    admin.activo = True
    admin.user.is_active = True
    admin.user.save()
    admin.save()
    nombre = admin.user.get_full_name() or admin.user.username
    messages.success(request, f'Usuario {nombre} reactivado correctamente.')
    return redirect('usuario_list')