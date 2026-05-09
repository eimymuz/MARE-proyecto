import requests


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


def obtener_clima():
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": 19.1956894,
            "longitude": -104.6843221,
            "current": "temperature_2m,wind_speed_10m,wind_direction_10m,cloud_cover,weather_code",
            "timezone": "America/Mexico_City"
        }

        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})

        codigo_clima = current.get("weather_code")

        return {
            "temperatura": current.get("temperature_2m", "--"),
            "viento": current.get("wind_speed_10m", "--"),
            "direccion_viento": current.get("wind_direction_10m", "--"),
            "nubosidad": current.get("cloud_cover", "--"),
            "descripcion": interpretar_clima(codigo_clima),
        }

    except Exception as e:
        print("ERROR CLIMA:", e)

        return {
            "temperatura": "--",
            "viento": "--",
            "direccion_viento": "--",
            "nubosidad": "--",
            "descripcion": "No disponible",
        }