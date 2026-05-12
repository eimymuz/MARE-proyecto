import requests


# =========================================
# INTERPRETAR DESCRIPCIÓN DEL CLIMA
# =========================================

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


# =========================================
# ICONOS DINÁMICOS SEGÚN EL CLIMA
# =========================================

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


# =========================================
# ALERTAS DE VIENTO
# =========================================

def obtener_alerta_viento(viento):
    try:
        viento = float(viento)

    except:
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

# =========================================
# OBTENER CLIMA DESDE OPEN-METEO
# =========================================

def obtener_clima():
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": 19.1956894,
            "longitude": -104.6843221,

            "current":
                "temperature_2m,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "cloud_cover,"
                "weather_code",

            "timezone": "America/Mexico_City"
        }

        response = requests.get(
            url,
            params=params,
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        current = data.get("current", {})

        codigo_clima = current.get("weather_code")

        viento = current.get("wind_speed_10m", "--")

        return {
            "temperatura":
                current.get("temperature_2m", "--"),

            "viento":
                viento,

            "direccion_viento":
                current.get("wind_direction_10m", "--"),

            "nubosidad":
                current.get("cloud_cover", "--"),

            "descripcion":
                interpretar_clima(codigo_clima),

            "icono":
                obtener_icono_clima(codigo_clima),

            "alerta_viento":
                obtener_alerta_viento(viento),
        }

    except Exception as e:

        print("ERROR CLIMA:", e)

        return {
            "temperatura": "--",
            "viento": "--",
            "direccion_viento": "--",
            "nubosidad": "--",

            "descripcion":
                "No disponible",

            "icono":
                "🌤️",

            "alerta_viento": {
                "nivel": "sin-datos",
                "texto": "No hay datos disponibles sobre el viento."
            }
        }