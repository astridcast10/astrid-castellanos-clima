import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Clima HN", layout="wide", initial_sidebar_state="expanded")

CIUDADES = {
    "Tegucigalpa":      (14.0818, -87.2068),
    "San Pedro Sula":   (15.5000, -88.0333),
    "Villanueva":       (15.3167, -87.9500),
    "La Ceiba":         (15.7794, -86.7936),
    "Choloma":          (15.6167, -87.9500),
    "El Progreso":      (15.4000, -87.8000),
    "Choluteca":        (13.3000, -87.2000),
    "Comayagua":        (14.4500, -87.6333),
    "Siguatepeque":     (14.5979, -87.8325),
    "Santa Rosa de Copan": (14.7667, -88.7833),
    "Danli":            (14.0333, -86.5833),
    "Juticalpa":        (14.6667, -86.2167),
    "Tela":             (15.7833, -87.4500),
    "Trujillo":         (15.9167, -85.9667),
    "Puerto Cortes":    (15.8500, -87.9333),
}

WMO_CODES = {
    0: "Cielo despejado",
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
    65: "Lluvia fuerte",
    71: "Nieve ligera",
    73: "Nieve moderada",
    75: "Nieve fuerte",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos fuertes",
    95: "Tormenta electrica",
    99: "Tormenta con granizo",
}

def wind_direction_label(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    return dirs[round(deg / 45) % 8]

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "weather_code", "wind_speed_10m", "wind_direction_10m",
            "precipitation", "surface_pressure",
        ],
        "hourly": ["temperature_2m", "precipitation_probability"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code"],
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
        return None

if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"
if "historial" not in st.session_state:
    st.session_state.historial = []
if "ciudad_activa" not in st.session_state:
    st.session_state.ciudad_activa = "Tegucigalpa"

with st.sidebar:
    st.title("Clima HN")
    st.write("Honduras")
    st.divider()

    if st.button("Inicio", use_container_width=True):
        st.session_state.pagina = "Inicio"
    if st.button("Consultar clima", use_container_width=True):
        st.session_state.pagina = "Consultar"
    if st.button("Historial", use_container_width=True):
        st.session_state.pagina = "Historial"
    if st.button("Acerca de", use_container_width=True):
        st.session_state.pagina = "Acerca"

    st.divider()
    st.caption("Datos: Open-Meteo API")

pagina = st.session_state.pagina

if pagina == "Inicio":
    st.title("Clima en Honduras")
    st.write("Consulta el clima actual y el pronostico de los proximos 7 dias para las principales ciudades de Honduras.")
    st.divider()

    col_info, col_consulta = st.columns([1.2, 1])

    with col_info:
        st.subheader("Resumen rapido — Tegucigalpa")
        data = get_weather(*CIUDADES["Tegucigalpa"])
        if data:
            cur = data["current"]
            condicion = WMO_CODES.get(cur["weather_code"], "Desconocido")
            st.write(f"**Condicion:** {condicion}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Temperatura", f"{cur['temperature_2m']:.1f} °C")
            m2.metric("Humedad", f"{cur['relative_humidity_2m']} %")
            m3.metric("Viento", f"{cur['wind_speed_10m']:.1f} km/h")

    with col_consulta:
        st.subheader("Consulta rapida")
        ciudad_rapida = st.selectbox("Ciudad", list(CIUDADES.keys()), key="inicio_ciudad")
        if st.button("Ver clima", use_container_width=True):
            st.session_state.ciudad_activa = ciudad_rapida
            if ciudad_rapida not in st.session_state.historial:
                st.session_state.historial.append(ciudad_rapida)
            st.session_state.pagina = "Consultar"
            st.rerun()

elif pagina == "Consultar":
    col_principal, col_derecha = st.columns([2, 1])

    with col_principal:
        st.title("Consultar clima")
        ciudad = st.selectbox("Seleccionar ciudad", list(CIUDADES.keys()),
                              index=list(CIUDADES.keys()).index(st.session_state.ciudad_activa))

        if ciudad != st.session_state.ciudad_activa:
            st.session_state.ciudad_activa = ciudad

        if ciudad not in st.session_state.historial:
            st.session_state.historial.append(ciudad)

        lat, lon = CIUDADES[ciudad]
        data = get_weather(lat, lon)

        if not data:
            st.stop()

        cur = data["current"]
        daily = data["daily"]
        hourly = data["hourly"]

        temp     = cur["temperature_2m"]
        feels    = cur["apparent_temperature"]
        humidity = cur["relative_humidity_2m"]
        wind_spd = cur["wind_speed_10m"]
        wind_dir = wind_direction_label(cur["wind_direction_10m"])
        precip   = cur["precipitation"]
        pressure = cur["surface_pressure"]
        condicion = WMO_CODES.get(cur["weather_code"], "Desconocido")

        st.write(f"**{condicion}** — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.divider()

        st.subheader("Condiciones actuales")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura", f"{temp:.1f} °C")
        c2.metric("Sensacion termica", f"{feels:.1f} °C")
        c3.metric("Humedad", f"{humidity} %")
        c4.metric("Viento", f"{wind_spd:.1f} km/h {wind_dir}")

        c5, c6 = st.columns(2)
        c5.metric("Precipitacion", f"{precip:.1f} mm")
        c6.metric("Presion atmosferica", f"{pressure:.0f} hPa")

        st.divider()
        st.subheader("Temperatura proximas 24 horas")
        horas   = [h[11:16] for h in hourly["time"][:24]]
        temps_h = hourly["temperature_2m"][:24]

        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=horas, y=temps_h,
            mode="lines+markers",
            line=dict(color="#0ea5e9", width=2),
            fill="tozeroy",
            fillcolor="rgba(14,165,233,0.1)",
        ))
        fig_temp.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title="Hora"),
            yaxis=dict(title="°C"),
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        st.subheader("Probabilidad de lluvia (proximas 24h)")
        prob_lluvia = hourly["precipitation_probability"][:24]

        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(x=horas, y=prob_lluvia, marker_color="#6366f1"))
        fig_rain.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title="Hora"),
            yaxis=dict(title="%", range=[0, 100]),
        )
        st.plotly_chart(fig_rain, use_container_width=True)

        st.divider()
        st.subheader("Pronostico 7 dias")
        dias_fmt = [datetime.strptime(d, "%Y-%m-%d").strftime("%a %d/%m") for d in daily["time"]]

        fig_7d = go.Figure()
        fig_7d.add_trace(go.Bar(x=dias_fmt, y=daily["temperature_2m_max"], name="Max", marker_color="#f97316"))
        fig_7d.add_trace(go.Bar(x=dias_fmt, y=daily["temperature_2m_min"], name="Min", marker_color="#38bdf8"))
        fig_7d.update_layout(
            barmode="group",
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(title="°C"),
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_7d, use_container_width=True)

        df_daily = pd.DataFrame({
            "Dia": dias_fmt,
            "Max (°C)": daily["temperature_2m_max"],
            "Min (°C)": daily["temperature_2m_min"],
            "Lluvia (mm)": daily["precipitation_sum"],
            "Condicion": [WMO_CODES.get(c, "—") for c in daily["weather_code"]],
        })
        st.dataframe(df_daily, use_container_width=True, hide_index=True)

    with col_derecha:
        st.title("Datos de consulta")
        st.write(f"**Ciudad:** {ciudad}")
        st.write(f"**Departamento:** Honduras")
        st.write(f"**Coordenadas:** {lat:.4f}, {lon:.4f}")
        st.write(f"**Hora consulta:** {datetime.now().strftime('%H:%M:%S')}")
        st.divider()

        if data:
            cur = data["current"]
            st.subheader("Resumen actual")
            st.write(f"Temperatura: **{cur['temperature_2m']:.1f} °C**")
            st.write(f"Sensacion: **{cur['apparent_temperature']:.1f} °C**")
            st.write(f"Humedad: **{cur['relative_humidity_2m']} %**")
            st.write(f"Viento: **{cur['wind_speed_10m']:.1f} km/h {wind_direction_label(cur['wind_direction_10m'])}**")
            st.write(f"Precipitacion: **{cur['precipitation']:.1f} mm**")
            st.write(f"Presion: **{cur['surface_pressure']:.0f} hPa**")
            st.write(f"Condicion: **{WMO_CODES.get(cur['weather_code'], 'Desconocido')}**")
            st.divider()

            st.subheader("Esta semana")
            tmax_list = data["daily"]["temperature_2m_max"]
            tmin_list = data["daily"]["temperature_2m_min"]
            st.write(f"Temperatura maxima: **{max(tmax_list):.1f} °C**")
            st.write(f"Temperatura minima: **{min(tmin_list):.1f} °C**")
            st.write(f"Lluvia total estimada: **{sum(data['daily']['precipitation_sum']):.1f} mm**")
            st.divider()

        if st.button("Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

elif pagina == "Historial":
    st.title("Historial de consultas")
    st.write("Ciudades que has consultado en esta sesion.")
    st.divider()

    if not st.session_state.historial:
        st.info("Todavia no has consultado ninguna ciudad.")
    else:
        for i, c in enumerate(st.session_state.historial, 1):
            col_h, col_btn = st.columns([3, 1])
            col_h.write(f"{i}. {c}")
            if col_btn.button("Ver", key=f"hist_{i}"):
                st.session_state.ciudad_activa = c
                st.session_state.pagina = "Consultar"
                st.rerun()

        st.divider()
        if st.button("Limpiar historial"):
            st.session_state.historial = []
            st.rerun()

elif pagina == "Acerca":
    st.title("Acerca de esta aplicacion")
    st.divider()
    st.write("Clima HN es una aplicacion web desarrollada con Python y Streamlit que muestra informacion meteorologica en tiempo real para las principales ciudades de Honduras.")
    st.write("Utiliza la API publica de Open-Meteo, la cual no requiere registro ni clave de acceso.")
    st.divider()
    st.subheader("Tecnologias utilizadas")
    st.write("- Python")
    st.write("- Streamlit")
    st.write("- Open-Meteo API")
    st.write("- Plotly")
    st.write("- Pandas")
    st.divider()
    st.subheader("Fuente de datos")
    st.write("Open-Meteo — https://open-meteo.com")
    st.write("Modelos meteorologicos de proveedores nacionales como DWD, NOAA y ECMWF.")
    st.divider()
    st.caption("Computacion en la Nube — Universidad Tecnologica de Honduras (UTH)")
