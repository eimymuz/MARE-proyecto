from django.urls import path
from . import views

urlpatterns = [
    path('',          views.landing,          name='landing'),
    path('solicitar/', views.solicitud_submit, name='solicitud_submit'),
]