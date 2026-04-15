# ⚓ MARE (Manejador Administrativo y Registro de Embarcaciones)

Sistema de información con características web para una marina privada que integre un administrador de reservaciones con un mapa interactivo cuasi-realista de la marina, con el objetivo de mejorar la planeación, visualización y asignación de espacios para embarcaciones. 

---

## 📄 Descripción



---

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

---

## 🏗️ Arquitectura

El sistema se basa en una arquitectura cliente-servidor, donde los usuarios interactúan con la aplicación a través de un navegador web.

- Cliente y administrador acceden vía navegador  
- Comunicación mediante HTTPS  
- Lógica central en Django  
- Base de datos relacional  

---

## 📁 Estructura del proyecto

plaintext
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


---

## 📄 Licencia 
Proyecto académico para la materia de Ingeniería en Software.