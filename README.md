# ⚓ MARE (Manejador Administrativo y Registro de Embarcaciones)
Sistema de información con características web para una marina privada que integre un administrador de reservaciones con un mapa interactivo cuasi-realista de la marina, con el objetivo de mejorar la planeación, visualización y asignación de espacios para embarcaciones. 


## 📄 Descripción
MARE es una plataforma diseñada para facilitar la administración de espacios en una marina. Permite gestionar solicitudes de atraque, asignación de muelles, registro de clientes y control de embarcaciones.

El sistema está orientado a optimizar la organización y mejorar la eficiencia operativa mediante una interfaz administrativa clara y un flujo estructurado de gestión.


## 🎯 Caso de estudio
El sistema se basa en la *Marina Puerto de la Navidad (Colima, México)*.

### Problemática principal:
- Falta de visualización del espacio  
- Gestión manual de datos  
- Asignación basada en memoria  
- Dificultad para planear ocupación  

### Solución:
✔ Sistema web centralizado  
✔ Mapa interactivo de muelles  
✔ Asignación visual con colores  
✔ Filtros por fechas  


## 🏗️ Arquitectura
El sistema se basa en una arquitectura cliente-servidor, donde los usuarios interactúan con la aplicación a través de un navegador web.

- Cliente y administrador acceden vía navegador  
- Comunicación mediante HTTPS  
- Lógica central en Django  
- Base de datos relacional  


## ⚙️ Funcionalidades principales
### 👤 Cliente
- Registro de solicitud de reservación
- Captura de datos personales y de embarcación
- Consulta de información general de la marina

### 🧑‍💼 Administrador
- Gestión de solicitudes (aceptar, rechazar)
- Administración de reservaciones
- Asignación de espacios en muelles
- Visualización de ocupación mediante mapa
- Filtrado por fechas y características


## 📁 Estructura del proyecto

```plaintext
MARE_PROYECTO/
├── apps/
│   ├── asignaciones/
│   ├── clientes/
│   ├── embarcaciones/
│   ├── mapa/
│   ├── muelles/
│   ├── publico/
│   └── solicitudes/
│
├── config/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
├── .env
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── requirements.txt
└── README.md
```

## 🧪 Metodología
El proyecto fue desarrollado utilizando el modelo en cascada, el cual organiza el desarrollo en fases secuenciales:

- Análisis
- Diseño
- Desarrollo
- Pruebas
- Implementación

Este enfoque permite un control estructurado del proyecto y una documentación clara en cada etapa .


## 🚀 Estado del proyecto
En desarrollo.
Actualmente se trabaja en la implementación del sistema web con la visualización interactiva del mapa.


## 📄 Licencia 
Proyecto académico para la materia de Ingeniería en SoftwareG