import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="ClimaCast",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main { background-color: #0f172a; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .app-header {
        text-align: center;
        padding: 2rem 0 1.5rem;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 2rem;
    }
    .app-header h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .app-header p {
        color: #64748b;
        font-size: 1rem;
        margin-top: 0.4rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.4rem 1.2rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .metric-card:hover { border-color: #38bdf8; }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1;
    }
    .metric-unit {
        font-size: 1rem;
        color: #38bdf8;
        font-weight: 500;
    }
    .metric-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }

    .condition-chip {
        display: inline-block;
        background: #0ea5e9;
        color: #fff;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.3rem 1rem;
        border-radius: 999px;
        margin-top: 0.5rem;
    }

    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #cbd5e1;
        margin: 1.8rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #1e293b;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] label { color: #94a3b8 !important; }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


CIUDADES = {
    "Tegucigalpa, Honduras":   (14.0818, -87.2068),
    "San Pedro Sula, Honduras":(15.5000, -88.0333),
    "Villanueva, Honduras":    (15.3167, -87.9500),
    "Ciudad de México, México":(19.4326, -99.1332),
    "Bogotá, Colombia":        (4.7110,  -74.0721),
    "Buenos Aires, Argentina": (-34.6037,-58.3816),
    "Lima, Perú":              (-12.0464,-77.0428),
    "Madrid, España":          (40.4168, -3.7038),
    "Nueva York, EE.UU.":      (40.7128, -74.0060),
    "Tokyo, Japón":            (35.6762, 139.6503),
}

WMO_CODES = {
    0: ("Despejado ☀️", "☀️"),
    1: ("Mayormente despejado 🌤️", "🌤️"),
    2: ("Parcialmente nublado ⛅", "⛅"),
    3: ("Nublado ☁️", "☁️"),
    45: ("Niebla 🌫️", "🌫️"),
    48: ("Niebla con escarcha 🌫️", "🌫️"),
    51: ("Llovizna ligera 🌦️", "🌦️"),
    53: ("Llovizna moderada 🌦️", "🌦️"),
    55: ("Llovizna intensa 🌧️", "🌧️"),
    61: ("Lluvia ligera 🌧️", "🌧️"),
    63: ("Lluvia moderada 🌧️", "🌧️"),
    65: ("Lluvia fuerte 🌧️", "🌧️"),
    71: ("Nieve ligera ❄️", "❄️"),
    73: ("Nieve moderada ❄️", "❄️"),
    75: ("Nieve fuerte ❄️", "❄️"),
    80: ("Chubascos ligeros 🌦️", "🌦️"),
    81: ("Chubascos moderados 🌧️", "🌧️"),
    82: ("Chubascos fuertes ⛈️", "⛈️"),
    95: ("Tormenta eléctrica ⛈️", "⛈️"),
    99: ("Tormenta con granizo ⛈️", "⛈️"),
}


@st.cache_data(ttl=600)
def get_weather(lat: float, lon: float) -> dict | None:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "weather_code", "wind_speed_10m", "wind_direction_10m",
            "precipitation", "surface_pressure", "visibility",
        ],
        "hourly": ["temperature_2m", "precipitation_probability", "wind_speed_10m"],
        "daily": [
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "weather_code",
        ],
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


def wind_direction_label(deg: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    return dirs[round(deg / 45) % 8]


with st.sidebar:
    st.markdown("### 🌍 Seleccionar ciudad")
    ciudad = st.selectbox("Ciudad", list(CIUDADES.keys()), index=1)

    st.markdown("---")
    ("""
    Actualización cada **10 min**
    """)
    st.markdown("---")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


st.markdown("""
<div class="app-header">
    <h1>🌤️ ClimaScope</h1>
    <p>Pronóstico meteorológico en tiempo real · Open-Meteo API</p>
</div>
""", unsafe_allow_html=True)

# Obtener datos
lat, lon = CIUDADES[ciudad]
data = get_weather(lat, lon)

if not data:
    st.stop()

cur = data["current"]
daily = data["daily"]
hourly = data["hourly"]

wcode = cur.get("weather_code", 0)
cond_label, cond_icon = WMO_CODES.get(wcode, ("Desconocido", "🌡️"))
temp = cur["temperature_2m"]
feels = cur["apparent_temperature"]
humidity = cur["relative_humidity_2m"]
wind_spd = cur["wind_speed_10m"]
wind_dir = wind_direction_label(cur["wind_direction_10m"])
precip = cur["precipitation"]
pressure = cur["surface_pressure"]

# ciudad actual
st.markdown(f"### 📍 {ciudad}")
st.markdown(f'<span class="condition-chip">{cond_label}</span>', unsafe_allow_html=True)
st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

cols = st.columns(4)
metrics = [
    ("🌡️", "Temperatura", f"{temp:.1f}", "°C"),
    ("🤔", "Sensación térmica", f"{feels:.1f}", "°C"),
    ("💧", "Humedad", f"{humidity}", "%"),
    ("💨", "Viento", f"{wind_spd:.1f}", f"km/h {wind_dir}"),
]
for col, (icon, label, val, unit) in zip(cols, metrics):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val} <span class="metric-unit">{unit}</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
cols2 = st.columns(4)
metrics2 = [
    ("🌧️", "Precipitación", f"{precip:.1f}", "mm"),
    ("🔵", "Presión", f"{pressure:.0f}", "hPa"),
    ("📍", "Latitud", f"{lat:.4f}", "°"),
    ("📍", "Longitud", f"{lon:.4f}", "°"),
]
for col, (icon, label, val, unit) in zip(cols2, metrics2):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val} <span class="metric-unit">{unit}</span></div>
    </div>
    """, unsafe_allow_html=True)


# ── Pronóstico por hora (próximas 24h) ────────────────────────────────────────
st.markdown('<div class="section-title">📈 Temperatura próximas 24 horas</div>', unsafe_allow_html=True)

horas = hourly["time"][:24]
temps_h = hourly["temperature_2m"][:24]
prob_lluvia = hourly["precipitation_probability"][:24]
viento_h = hourly["wind_speed_10m"][:24]

df_hourly = pd.DataFrame({
    "Hora": [h[11:16] for h in horas],
    "Temperatura (°C)": temps_h,
    "Prob. lluvia (%)": prob_lluvia,
    "Viento (km/h)": viento_h,
})

fig_temp = go.Figure()
fig_temp.add_trace(go.Scatter(
    x=df_hourly["Hora"],
    y=df_hourly["Temperatura (°C)"],
    mode="lines+markers",
    line=dict(color="#38bdf8", width=2.5),
    marker=dict(size=5, color="#0ea5e9"),
    fill="tozeroy",
    fillcolor="rgba(56,189,248,0.08)",
    name="Temperatura",
))
fig_temp.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#1e293b", ticksuffix="°C"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=260,
    showlegend=False,
)
st.plotly_chart(fig_temp, use_container_width=True)

# Probabilidad de lluvia
st.markdown('<div class="section-title">🌧️ Probabilidad de lluvia (próximas 24h)</div>', unsafe_allow_html=True)
fig_rain = go.Figure()
fig_rain.add_trace(go.Bar(
    x=df_hourly["Hora"],
    y=df_hourly["Prob. lluvia (%)"],
    marker_color="#6366f1",
    marker_line_width=0,
    name="Prob. lluvia",
))
fig_rain.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    xaxis=dict(gridcolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", ticksuffix="%", range=[0, 100]),
    margin=dict(l=0, r=0, t=10, b=0),
    height=220,
    showlegend=False,
)
st.plotly_chart(fig_rain, use_container_width=True)


# Pronóstico 7 días
st.markdown('<div class="section-title">📅 Pronóstico 7 días</div>', unsafe_allow_html=True)

dias_raw = daily["time"]
tmax = daily["temperature_2m_max"]
tmin = daily["temperature_2m_min"]
precip_d = daily["precipitation_sum"]
wcodes_d = daily["weather_code"]

dias_fmt = []
for d in dias_raw:
    dt = datetime.strptime(d, "%Y-%m-%d")
    dias_fmt.append(dt.strftime("%a %d/%m"))

df_daily = pd.DataFrame({
    "Día": dias_fmt,
    "Máx (°C)": tmax,
    "Mín (°C)": tmin,
    "Lluvia (mm)": precip_d,
    "Condición": [WMO_CODES.get(c, ("—", "—"))[0] for c in wcodes_d],
})

# Gráfico barras max/min
fig_7d = go.Figure()
fig_7d.add_trace(go.Bar(
    x=df_daily["Día"], y=df_daily["Máx (°C)"],
    name="Máx", marker_color="#f97316", marker_line_width=0,
))
fig_7d.add_trace(go.Bar(
    x=df_daily["Día"], y=df_daily["Mín (°C)"],
    name="Mín", marker_color="#38bdf8", marker_line_width=0,
))
fig_7d.update_layout(
    barmode="group",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    xaxis=dict(gridcolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", ticksuffix="°C"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=260,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
st.plotly_chart(fig_7d, use_container_width=True)

# Tabla resumen
st.dataframe(
    df_daily,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Máx (°C)": st.column_config.NumberColumn(format="%.1f °C"),
        "Mín (°C)": st.column_config.NumberColumn(format="%.1f °C"),
        "Lluvia (mm)": st.column_config.NumberColumn(format="%.1f mm"),
    }
)