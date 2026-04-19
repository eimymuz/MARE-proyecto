# Usa Python 3.11 como imagen base
FROM python:3.11-slim

# Establece variables de entorno
# Previene que Python escriba archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Previene que Python almacene en buffer stdout y stderr
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app 

# Instala dependencias del sistema necesarias para PostgreSQL (Comnados basicos de linux que descragan e instalan paquetes)
RUN apt-get update && apt-get install -y \
  gcc \
  postgresql-client \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos (Copian la informacion que tenemos)
COPY requirements.txt /app/

# Instala las dependencias de Python | configura todo por defecto
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copia el código del proyecto | copaimos todo el contenido actual al contenedor
COPY . /app/

# Expone el puerto 8000 (puerto por defecto de Django) | ponemos todo el cotendio del cotnener en el puerto 800
EXPOSE 8000

# Comando por defecto para ejecutar el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]