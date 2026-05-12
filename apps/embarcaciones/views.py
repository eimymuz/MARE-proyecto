from django.shortcuts               import  render
from django.contrib.auth.decorators import login_required

# La gestión de clientes se realiza a través del formulario público
# (apps/publico) y el admin de Django (/admin/).
# No se implementó un CRUD propio para clientes en este proyecto.