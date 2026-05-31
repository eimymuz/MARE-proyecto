# =============================================================================
# services/marine_api.py — App: mapa
# Módulo de servicio que consulta la API externa Open-Meteo para obtener
# el clima actual de la ubicación de la marina.
#
# Funciones exportadas:
#   - obtener_clima()          → llamada principal; usada en views.py (vista inicio)
#   - interpretar_clima(codigo) → auxiliar interna
#   - obtener_icono_clima(codigo) → auxiliar interna
#   - obtener_alerta_viento(viento) → auxiliar interna
#
# Consumido por:
#   - apps/mapa/views.py → función inicio() → pasa el dict 'clima' a templates/inicio.html
#   - templates/inicio.html → muestra temperatura, viento, icono y alerta en el dashboard
#
# Coordenadas hardcodeadas: lat 19.1956894, lon -104.6843221 (ubicación de la marina)
# API: Open-Meteo (https://api.open-meteo.com) — sin autenticación, gratuita
# Timeout: 8 segundos; si falla retorna valores "--" para no bloquear la carga del dashboard
# =============================================================================

import requests


# =============================================================================
# interpretar_clima
# Traduce el código numérico WMO weather_code de Open-Meteo a una descripción
# en español legible. Los códigos siguen el estándar WMO 4677.
# Retorna "Condición no disponible" si el código no está en el diccionario.
# Usado internamente en obtener_clima().
# =============================================================================
def interpretar_clima(codigo):
    codigos = {
        0: "Despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos fuertes",
        95: "Tormenta",
    }

    return codigos.get(codigo, "Condición no disponible")


# =============================================================================
# obtener_icono_clima
# Mapea el mismo código WMO a un emoji de icono para mostrar visualmente
# en el widget de clima del dashboard (inicio.html).
# Retorna "🌤️" como fallback si el código no está en el diccionario.
# Usado internamente en obtener_clima().
# =============================================================================
def obtener_icono_clima(codigo):
    iconos = {
        0: "☀️",
        1: "🌤️",
        2: "⛅",
        3: "☁️",
        45: "🌫️",
        48: "🌫️",
        51: "🌦️",
        53: "🌦️",
        55: "🌧️",
        61: "🌧️",
        63: "🌧️",
        65: "🌧️",
        80: "🌦️",
        81: "🌧️",
        82: "⛈️",
        95: "⛈️",
    }

    return iconos.get(codigo, "🌤️")


# =============================================================================
# obtener_alerta_viento
# Clasifica la velocidad de viento (km/h) en niveles de alerta para la marina.
# Retorna un dict con 'nivel' (normal/moderado/precaucion/peligro/sin-datos)
# y 'texto' con la recomendación operativa.
# Los umbrales están basados en la escala Beaufort para navegación de recreo.
# Usado internamente en obtener_clima(); el dict completo se pasa a inicio.html.
# =============================================================================
def obtener_alerta_viento(viento):
    try:
        viento = float(viento)
    except:
        # Si el dato de viento no es numérico (ej: "--" por fallo de API)
        return {
            "nivel": "sin-datos",
            "texto": "No hay datos disponibles sobre el viento."
        }

    if viento >= 110:
        return {
            "nivel": "peligro",
            "texto": "Viento huracanado. No se debe navegar bajo ninguna circunstancia."
        }

    if viento >= 62:
        return {
            "nivel": "peligro",
            "texto": "Temporal peligroso. Suspender navegación y revisar amarres."
        }

    if viento >= 40:
        return {
            "nivel": "peligro",
            "texto": "Viento fuerte. Riesgo alto para navegación de recreo."
        }

    if viento >= 37:
        return {
            "nivel": "precaucion",
            "texto": "Límite de seguridad. Navegación incómoda; operar con precaución."
        }

    if viento >= 20:
        return {
            "nivel": "moderado",
            "texto": "Viento moderado. Mantener vigilancia en maniobras y atraques."
        }

    return {
        "nivel": "normal",
        "texto": "Viento estable. Condiciones favorables para operación normal."
    }


# =============================================================================
# obtener_clima
# Función principal del módulo. Realiza un GET a Open-Meteo con las
# coordenadas de la marina y retorna un dict con los datos procesados.
#
# Retorna dict con:
#   temperatura      → °C actual (temperature_2m)
#   viento           → km/h actual (wind_speed_10m)
#   direccion_viento → grados (wind_direction_10m)
#   nubosidad        → % (cloud_cover)
#   descripcion      → string legible vía interpretar_clima()
#   icono            → emoji vía obtener_icono_clima()
#   alerta_viento    → dict {nivel, texto} vía obtener_alerta_viento()
#
# Si la petición falla (timeout, red, etc.) captura la excepción, la imprime
# en consola y retorna valores "--" para no bloquear el render de inicio.html.
# =============================================================================
def obtener_clima():
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude":  19.1956894,    # Latitud de la marina
            "longitude": -104.6843221,  # Longitud de la marina

            "current":
                "temperature_2m,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "cloud_cover,"
                "weather_code",

            "timezone": "America/Mexico_City"  # Para que las horas correspondan a la zona local
        }

        response = requests.get(
            url,
            params=params,
            timeout=8  # Evita bloquear el dashboard si la API tarda demasiado
        )

        response.raise_for_status()  # Lanza excepción si el status HTTP es 4xx o 5xx

        data    = response.json()
        current = data.get("current", {})

        codigo_clima = current.get("weather_code")
        viento       = current.get("wind_speed_10m", "--")

        return {
            "temperatura":      current.get("temperature_2m", "--"),
            "viento":           viento,
            "direccion_viento": current.get("wind_direction_10m", "--"),
            "nubosidad":        current.get("cloud_cover", "--"),
            "descripcion":      interpretar_clima(codigo_clima),
            "icono":            obtener_icono_clima(codigo_clima),
            "alerta_viento":    obtener_alerta_viento(viento),
        }

    except Exception as e:
        print("ERROR CLIMA:", e)  # Log en consola del servidor; no bloquea al usuario

        # Valores de fallback seguros para que inicio.html no rompa al acceder a clima.X
        return {
            "temperatura":      "--",
            "viento":           "--",
            "direccion_viento": "--",
            "nubosidad":        "--",
            "descripcion":      "No disponible",
            "icono":            "🌤️",
            "alerta_viento": {
                "nivel": "sin-datos",
                "texto": "No hay datos disponibles sobre el viento."
            }
        }