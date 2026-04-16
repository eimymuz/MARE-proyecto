from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from apps.muelles.models import Espacio, EtiquetaMuelle, ZonaTierra
from apps.asignaciones.models import Asignacion, Administrador
from apps.solicitudes.models import Solicitud


@login_required
def inicio(request):
    return render(request, 'inicio.html', {})