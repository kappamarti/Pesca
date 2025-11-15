import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import requests
import json
import os

# Configurazione della pagina per mobile
st.set_page_config(
    page_title="Pesca Lombardia",
    page_icon="🎣",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nascondi elementi di Streamlit per mobile
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.css-1d391kg {padding: 1rem 1rem;}
.block-container {padding-top: 2rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

current_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); color: white; padding: 5px 15px; border-radius: 10px; z-index: 9999; font-family: monospace; font-size: 14px; font-weight: bold;">
🕐 {current_time}
</div>
""", unsafe_allow_html=True)
# Coordinate precise delle zone di pesca richieste
ZONE_COORDINATES = {
    'Ticino - Sesto Calende': {'lat': 45.7286, 'lon': 8.6358},
    'Lago Maggiore - Lombardia': {'lat': 45.9000, 'lon': 8.6500},
    'Lago di Varese': {'lat': 45.8167, 'lon': 8.7333},
    'Ticino - Pavia': {'lat': 45.1865, 'lon': 9.1571}
}

# Calendario aperture pesca in Lombardia (Regolamento Regionale) - AGGIORNATO 2025
FISHING_CALENDAR = {
    'Trota Fario': {
        'apertura': date(2025, 3, 1),
        'chiusura': date(2025, 9, 30),
        'note': 'Misura minima 22 cm - Limite giornaliero 5 esemplari',
        'zone': ['Ticino - Sesto Calende', 'Ticino - Pavia']
    },
    'Luccio': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 50 cm - Divieto di pesca dal 15/03 al 31/05',
        'zone': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Ticino - Sesto Calende']
    },
    'Carpa': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Nessuna misura minima - No limite giornaliero',
        'zone': ['Lago di Varese', 'Ticino - Pavia', 'Lago Maggiore - Lombardia']
    },
    'Persico Reale': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 18 cm - Limite giornaliero 10 esemplari',
        'zone': ['Lago Maggiore - Lombardia', 'Lago di Varese']
    },
    'Siluro': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Nessuna misura minima - Obbligo di rimozione',
        'zone': ['Ticino - Sesto Calende', 'Ticino - Pavia']
    },
    'Cavedano': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 15 cm - Limite giornaliero 20 esemplari',
        'zone': ['Ticino - Sesto Calende', 'Ticino - Pavia']
    },
    'Luccio Perca': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 18 cm - Limite giornaliero 10 esemplari',
        'zone': ['Lago Maggiore - Lombardia', 'Lago di Varese']
    },
    'Barbo': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 20 cm - Limite giornaliero 5 esemplari',
        'zone': ['Ticino - Sesto Calende', 'Ticino - Pavia']
    }
}

# Percorso immagini locali
def get_fish_image(fish_name):
    """Restituisce il percorso dell'immagine del pesce"""
    image_paths = {
        'Trota Fario': 'images/trota_fario.jpg',
        'Luccio': 'images/luccio.jpg',
        'Carpa': 'images/carpa.jpg',
        'Persico Reale': 'images/persico_reale.jpg',
        'Siluro': 'images/siluro.jpg',
        'Cavedano': 'images/cavedano.jpg',
        'Luccio Perca': 'images/luccio_perca.jpg',
        'Barbo': 'images/barbo.jpg'
    }
    
    path = image_paths.get(fish_name)
    if path and os.path.exists(path):
        return path
    else:
        return None

# Funzione per ottenere dati meteo reali da Open-Meteo (GRATUITA)
def get_real_weather_data(lat, lon, location_name):
    """Ottiene dati meteo reali da Open-Meteo - API Gratuita"""
    try:
        # API Open-Meteo - completamente gratuita con previsioni orarie
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,cloud_cover,weather_code&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m,pressure_msl&timezone=Europe/Rome&forecast_days=2"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return process_weather_data(data, location_name, lat, lon)
        else:
            return get_fallback_weather_data(location_name)
            
    except Exception as e:
        return get_fallback_weather_data(location_name)

def process_weather_data(data, location_name, lat, lon):
    """Elabora i dati meteo ricevuti dall'API Open-Meteo"""
    current = data['current']
    air_temp = current['temperature_2m']
    
    # Converti weather code in descrizione
    weather_condition = get_weather_description(current['weather_code'])
    
    # Processa le previsioni orarie con pressione
    hourly_data = process_hourly_forecast(data)
    
    weather_info = {
        'location': location_name,
        'temperature': round(air_temp, 1),
        'water_temperature': calculate_water_temperature(air_temp, current, location_name),
        'pressure': round(current['pressure_msl']),
        'humidity': current['relative_humidity_2m'],
        'wind_speed': round(current['wind_speed_10m'] * 3.6, 1),  # m/s to km/h
        'weather_condition': weather_condition,
        'weather_main': get_weather_main(current['weather_code']),
        'clouds': current['cloud_cover'],
        'visibility': 10,
        'hourly_forecast': hourly_data,
        'success': True
    }
    return weather_info

def process_hourly_forecast(data):
    """Processa le previsioni orarie per le prossime 6 ore con pressione"""
    hourly = data['hourly']
    current_time = datetime.now()
    
    forecast = []
    for i in range(len(hourly['time'])):
        hour_time = datetime.fromisoformat(hourly['time'][i].replace('Z', '+00:00'))
        
        # Prendiamo solo le prossime 6 ore
        if hour_time > current_time and len(forecast) < 6:
            forecast.append({
                'time': hour_time.strftime('%H:%M'),
                'temperature': round(hourly['temperature_2m'][i], 1),
                'pressure': round(hourly['pressure_msl'][i]),
                'precipitation_probability': hourly['precipitation_probability'][i],
                'weather_code': hourly['weather_code'][i],
                'weather_description': get_weather_description(hourly['weather_code'][i]),
                'wind_speed': round(hourly['wind_speed_10m'][i] * 3.6, 1)
            })
    
    return forecast

def get_weather_description(weather_code):
    """Converte weather code di Open-Meteo in descrizione"""
    weather_codes = {
        0: "Sereno",
        1: "Prevalentemente sereno", 
        2: "Parzialmente nuvoloso",
        3: "Nuvoloso",
        45: "Nebbia",
        48: "Nebbia con brina",
        51: "Pioviggine leggera",
        53: "Pioviggine moderata",
        55: "Pioviggine intensa",
        61: "Pioggia leggera",
        63: "Pioggia moderata",
        65: "Pioggia intensa",
        80: "Rovesci leggeri",
        81: "Rovesci moderati",
        82: "Rovesci intensi",
        95: "Temporale",
        96: "Temporale con grandine leggera",
        99: "Temporale con grandine intensa"
    }
    return weather_codes.get(weather_code, "Condizioni variabili")

def get_weather_main(weather_code):
    """Converte weather code in categoria principale"""
    if weather_code in [0, 1]:
        return "Clear"
    elif weather_code in [2, 3]:
        return "Clouds"
    elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "Rain"
    elif weather_code in [95, 96, 99]:
        return "Thunderstorm"
    else:
        return "Clouds"

def calculate_water_temperature(air_temp, current_data, location_name):
    """Calcola temperatura acqua unendo dati ARPA e influenze locali/meteo"""
    
    current_month = datetime.now().month
    
    # Dati ARPA medi temperatura acqua lombarda + range stagionale
    water_data = {
        # Mese: (temp_media, min_storico, max_storico)
        1: (5.5, 3, 7),    # Gennaio
        2: (6.0, 4, 8),    # Febbraio  
        3: (8.5, 6, 11),   # Marzo
        4: (12.5, 9, 16),  # Aprile
        5: (16.5, 13, 20), # Maggio
        6: (20.5, 17, 24), # Giugno
        7: (23.5, 20, 27), # Luglio
        8: (22.5, 19, 26), # Agosto
        9: (19.5, 16, 23), # Settembre
        10: (15.5, 12, 19), # Ottobre
        11: (11.5, 8, 15),  # Novembre
        12: (7.5, 5, 10)    # Dicembre
    }
    
    base_temp, min_hist, max_hist = water_data[current_month]
    
    # 1. INFLUENZA TEMPERATURA ARIA (30%)
    air_effect = (air_temp - base_temp) * 0.3
    
    # 2. INFLUENZA LOCATION (caratteristiche specifiche)
    location_effect = 0
    location_variability = 0.3  # default
    
    if "Sesto Calende" in location_name:
        location_effect = (air_temp - base_temp) * 0.4
        location_variability = 0.4
        if current_month in [6, 7, 8]:
            location_effect -= 1.5
    
    elif "Lago Maggiore" in location_name:
        location_effect = (air_temp - base_temp) * 0.15
        location_variability = 0.15
        if current_month in [6, 7, 8]:
            location_effect -= 2.0
    
    elif "Lago di Varese" in location_name:
        location_effect = (air_temp - base_temp) * 0.35
        location_variability = 0.35
        if current_month in [6, 7, 8]:
            location_effect += 2.5
    
    elif "Pavia" in location_name:
        location_effect = (air_temp - base_temp) * 0.3
        location_variability = 0.3
        if current_month in [6, 7, 8]:
            location_effect += 1.0
    
    # 3. INFLUENZA METEO CORRENTE
    weather_code = current_data['weather_code']
    weather_effect = 0
    
    if weather_code in [0, 1]:
        if current_month in [4, 5, 6, 7, 8, 9]:
            weather_effect += 1.0 + (location_variability * 2)
    
    elif weather_code in [61, 63, 65, 80, 81, 82]:
        weather_effect -= 0.8
    
    elif weather_code in [95, 96, 99]:
        weather_effect -= 1.2
    
    elif weather_code in [2, 3]:
        weather_effect -= 0.3
    
    # 4. CALCOLO TEMPERATURA FINALE
    water_temp = base_temp + air_effect + location_effect + weather_effect
    
    # 5. LIMITI REALISTICI
    absolute_min = max(2, min_hist - 2)
    absolute_max = min(28, max_hist + 2)
    
    water_temp = max(absolute_min, min(absolute_max, water_temp))
    
    # 6. ARROTONDAMENTO
    water_temp = round(water_temp, 1)
    
    return water_temp

def get_fallback_weather_data(location_name):
    """Dati di fallback se l'API non funziona"""
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:
        temp = np.random.randint(0, 8)
        water_temp = max(2, temp - 2)
        weather_cond = np.random.choice(['Nuvoloso', 'Sereno', 'Nebbia'])
    elif current_month in [6, 7, 8]:
        temp = np.random.randint(22, 32)
        water_temp = temp - 3
        weather_cond = np.random.choice(['Sereno', 'Parzialmente nuvoloso', 'Temporale'])
    else:
        temp = np.random.randint(10, 20)
        water_temp = temp - 2
        weather_cond = np.random.choice(['Nuvoloso', 'Pioggia leggera', 'Sereno'])
    
    if "Sesto Calende" in location_name:
        water_temp -= 1
    elif "Lago di Varese" in location_name:
        water_temp += 1
    
    # Previsioni orarie fallback con pressione
    hourly_forecast = []
    current_hour = datetime.now().hour
    base_pressure = np.random.randint(1005, 1025)
    
    for i in range(6):
        hour = (current_hour + i + 1) % 24
        pressure = base_pressure + np.random.randint(-3, 4)
            
        hourly_forecast.append({
            'time': f"{hour:02d}:00",
            'temperature': temp + np.random.randint(-2, 3),
            'pressure': pressure,
            'precipitation_probability': np.random.randint(0, 30),
            'weather_description': weather_cond,
            'wind_speed': np.random.randint(5, 15)
        })
    
    return {
        'location': location_name,
        'temperature': temp,
        'water_temperature': water_temp,
        'pressure': base_pressure,
        'humidity': np.random.randint(50, 85),
        'wind_speed': np.random.randint(5, 20),
        'weather_condition': weather_cond,
        'weather_main': 'Clouds',
        'clouds': np.random.randint(20, 80),
        'visibility': np.random.randint(5, 15),
        'hourly_forecast': hourly_forecast,
        'success': False
    }

# Funzione per calcolare la fase lunare
def get_moon_phase():
    today = date.today()
    days_in_cycle = 29.53
    known_new_moon = date(2024, 1, 11)
    days_since_new = (today - known_new_moon).days
    moon_age = days_since_new % days_in_cycle
    
    if moon_age < 1: return "🌑 Luna Nuova"
    elif moon_age < 7: return "🌒 Luna Crescente"
    elif moon_age < 14: return "🌓 Primo Quarto"
    elif moon_age < 21: return "🌕 Luna Piena"
    else: return "🌗 Ultimo Quarto"

# Database delle specie ittiche specifiche per le tue zone
FISH_SPECIES = {
    'Trota Fario': {
        'temp_min': 8,
        'temp_max': 18,
        'pressure_low': 1000,
        'pressure_high': 1020,
        'moon_best': ['🌑 Luna Nuova', '🌕 Luna Piena'],
        'season_best': ['Primavera', 'Autunno'],
        'active_hours': ['mattina', 'sera'],
        'habitat': ['Ticino - Sesto Calende', 'Ticino - Pavia'],
        'esche': ['Camoscio', 'Lombrico', 'Artificiali'],
        'tecniche': ['Spinning', 'Mosca'],
        'zone_preferite': ['Ticino - Sesto Calende']
    },
    'Luccio': {
        'temp_min': 10,
        'temp_max': 22,
        'pressure_low': 1005,
        'pressure_high': 1025,
        'moon_best': ['🌒 Luna Crescente', '🌓 Primo Quarto'],
        'season_best': ['Primavera', 'Autunno'],
        'active_hours': ['alba', 'tramonto'],
        'habitat': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Ticino - Sesto Calende'],
        'esche': ['Cucchiaini', 'Siluri', 'Esche vive'],
        'tecniche': ['Spinning', 'Traina'],
        'zone_preferite': ['Lago Maggiore - Lombardia', 'Lago di Varese']
    },
    'Carpa': {
        'temp_min': 15,
        'temp_max': 25,
        'pressure_low': 1010,
        'pressure_high': 1030,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Estate', 'Primavera'],
        'active_hours': ['giorno', 'sera', 'notte'],
        'habitat': ['Lago di Varese', 'Ticino - Pavia'],
        'esche': ['Mais', 'Bolle', 'Paste'],
        'tecniche': ['Carpfishing', 'Feeder'],
        'zone_preferite': ['Lago di Varese', 'Ticino - Pavia']
    },
    'Persico Reale': {
        'temp_min': 12,
        'temp_max': 24,
        'pressure_low': 1008,
        'pressure_high': 1022,
        'moon_best': ['🌒 Luna Crescente', '🌓 Primo Quarto'],
        'season_best': ['Primavera', 'Estate'],
        'active_hours': ['mattina', 'pomeriggio'],
        'habitat': ['Lago Maggiore - Lombardia', 'Lago di Varese'],
        'esche': ['Camosci', 'Lombrici', 'Artificiali'],
        'tecniche': ['Spinning', 'Bolognese'],
        'zone_preferite': ['Lago Maggiore - Lombardia', 'Lago di Varese']
    },
    'Siluro': {
        'temp_min': 16,
        'temp_max': 28,
        'pressure_low': 1000,
        'pressure_high': 1020,
        'moon_best': ['🌑 Luna Nuova'],
        'season_best': ['Estate', 'Autunno'],
        'active_hours': ['sera', 'notte'],
        'habitat': ['Ticino - Sesto Calende', 'Ticino - Pavia'],
        'esche': ['Esche vive', 'Pesci morti'],
        'tecniche': ['Spinning', 'Traina', 'Fondo'],
        'zone_preferite': ['Ticino - Sesto Calende']
    },
    'Cavedano': {
        'temp_min': 10,
        'temp_max': 26,
        'pressure_low': 1005,
        'pressure_high': 1025,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Primavera', 'Estate'],
        'active_hours': ['giorno', 'tramonto'],
        'habitat': ['Ticino - Sesto Calende', 'Ticino - Pavia'],
        'esche': ['Lombrico', 'Mais', 'Paste'],
        'tecniche': ['Bolognese', 'Inglese'],
        'zone_preferite': ['Ticino - Pavia']
    },
    'Luccio Perca': {
        'temp_min': 14,
        'temp_max': 26,
        'pressure_low': 1008,
        'pressure_high': 1025,
        'moon_best': ['🌒 Luna Crescente', '🌓 Primo Quarto'],
        'season_best': ['Primavera', 'Estate', 'Autunno'],
        'active_hours': ['mattina', 'pomeriggio', 'sera'],
        'habitat': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Ticino - Sesto Calende'],
        'esche': ['Cucchiaini', 'Artificiali', 'Esche vive'],
        'tecniche': ['Spinning', 'Traina', 'Bolognese'],
        'zone_preferite': ['Lago Maggiore - Lombardia', 'Lago di Varese']
    },
    'Barbo': {
        'temp_min': 12,
        'temp_max': 24,
        'pressure_low': 1005,
        'pressure_high': 1020,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Primavera', 'Estate'],
        'active_hours': ['sera', 'notte'],
        'habitat': ['Ticino - Sesto Calende', 'Ticino - Pavia'],
        'esche': ['Lombrico', 'Bigattini', 'Paste', 'Mais'],
        'tecniche': ['Bolognese', 'Feeder', 'Fondo'],
        'zone_preferite': ['Ticino - Sesto Calende', 'Ticino - Pavia']
    }
}

# Stagioni
def get_season():
    today = date.today()
    month = today.month
    if month in [12, 1, 2]: return 'Inverno'
    elif month in [3, 4, 5]: return 'Primavera'
    elif month in [6, 7, 8]: return 'Estate'
    else: return 'Autunno'

# Calcolo punteggio attività pesci
def calculate_fish_activity(fish_species, weather, moon_phase, current_season, current_zone):
    score = 50  # Punteggio base
    
    # Temperatura acqua
    water_temp = weather['water_temperature']
    if fish_species['temp_min'] <= water_temp <= fish_species['temp_max']:
        score += 25
    elif abs(water_temp - (fish_species['temp_min'] + fish_species['temp_max'])/2) <= 3:
        score += 10
    else:
        score -= 20
    
    # Pressione atmosferica
    pressure = weather['pressure']
    if fish_species['pressure_low'] <= pressure <= fish_species['pressure_high']:
        score += 15
    else:
        score -= 10
    
    # Fase lunare
    if any(phase in moon_phase for phase in fish_species['moon_best']):
        score += 15
    
    # Stagione
    if current_season in fish_species['season_best']:
        score += 10
    
    # Zona preferita bonus
    if current_zone in fish_species['zone_preferite']:
        score += 10
    
    # Condizioni meteo
    if weather['weather_main'] in ['Clear', 'Clouds']:
        score += 5
    elif weather['weather_main'] in ['Rain', 'Drizzle']:
        score += 8
    
    return max(0, min(100, score))

# NAVIGAZIONE CON 2 TAB SEPARATI (ELIMINATE MAPPE)
st.title("🎣 Pesca Lombardia")

# Creiamo 2 tab separati (eliminato mappe)
tab1, tab2 = st.tabs(["🏠 Previsioni Pesca", "📅 Calendario"])

with tab1:
    st.header("📍 Seleziona Zona di Pesca")
    zona_selezionata = st.selectbox(
        "Scegli la tua zona di pesca:",
        list(ZONE_COORDINATES.keys()),
        key="zona_pesca"
    )

    # Recupera coordinate
    zone_info = ZONE_COORDINATES[zona_selezionata]
    lat = zone_info['lat']
    lon = zone_info['lon']

    # Bottone per aggiornare i dati
    if st.button("🔄 Aggiorna Dati Meteo", type="primary"):
        st.rerun()

    # Mostra caricamento e recupera dati
    with st.spinner(f'Recupero dati meteo per {zona_selezionata}...'):
        weather_data = get_real_weather_data(lat, lon, zona_selezionata)

    moon_phase = get_moon_phase()
    current_season = get_season()

    # Layout mobile-friendly - Condizioni attuali
    st.markdown("---")
    st.subheader(f"🌡️ Condizioni a {zona_selezionata}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Temperatura Aria", f"{weather_data['temperature']}°C")
        st.metric("Umidità", f"{weather_data['humidity']}%")

    with col2:
        st.metric("Temperatura Acqua", f"{weather_data['water_temperature']}°C")
        st.metric("Vento", f"{weather_data['wind_speed']} km/h")

    with col3:
        st.metric("Pressione", f"{weather_data['pressure']} hPa")
        st.metric("Nuvolosità", f"{weather_data['clouds']}%")

    # Info meteo e luna
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**Condizioni:** {weather_data['weather_condition']}")
        if not weather_data['success']:
            st.warning("⚠️ Dati simulati - Controlla connessione internet")
        else:
            st.success("✅ Dati in tempo reale")
    with col_info2:
        st.info(f"**{moon_phase}**")
        st.info(f"**Stagione:** {current_season}")

    # PREVISIONI ORARIE - CON PRESSIONE SENZA FRECCE
    st.markdown("---")
    st.subheader("⏰ Previsioni Prossime 6 Ore")

    if 'hourly_forecast' in weather_data and weather_data['hourly_forecast']:
        forecast_data = weather_data['hourly_forecast']
        
        # Crea colonne per ogni ora
        cols = st.columns(6)
        
        for i, hour_data in enumerate(forecast_data):
            with cols[i]:
                # Icona meteo in base alle condizioni
                if "Pioggia" in hour_data['weather_description'] or "Rovesci" in hour_data['weather_description']:
                    emoji = "🌧️"
                    color = "blue"
                elif "Temporale" in hour_data['weather_description']:
                    emoji = "⛈️"
                    color = "red"
                elif "Nuvoloso" in hour_data['weather_description']:
                    emoji = "☁️"
                    color = "gray"
                elif "Nebbia" in hour_data['weather_description']:
                    emoji = "🌫️"
                    color = "lightgray"
                else:
                    emoji = "☀️"
                    color = "orange"
                
                st.markdown(f"<h4 style='text-align: center; color: {color};'>{emoji}</h4>", unsafe_allow_html=True)
                st.markdown(f"<h5 style='text-align: center;'>{hour_data['time']}</h5>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>{hour_data['temperature']}°C</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 0.8em;'>{hour_data['weather_description']}</p>", unsafe_allow_html=True)
                
                # Pressione SENZA FRECCIA
                st.markdown(f"<p style='text-align: center; font-size: 0.8em;'>📊 {hour_data['pressure']} hPa</p>", unsafe_allow_html=True)
                
                # Mostra probabilità pioggia se significativa
                if hour_data['precipitation_probability'] > 20:
                    st.markdown(f"<p style='text-align: center; color: blue; font-size: 0.8em;'>💧 {hour_data['precipitation_probability']}%</p>", unsafe_allow_html=True)
                
                st.markdown(f"<p style='text-align: center; font-size: 0.8em;'>🌬️ {hour_data['wind_speed']} km/h</p>", unsafe_allow_html=True)

        # Analizza le previsioni per dare consigli
        rain_hours = [h for h in forecast_data if h['precipitation_probability'] > 50]
        good_hours = [h for h in forecast_data if h['precipitation_probability'] < 30 and "Sereno" in h['weather_description']]
        
        if rain_hours:
            st.warning(f"⚠️ **Attenzione pioggia**: Possibili precipitazioni alle {', '.join([h['time'] for h in rain_hours])}")
        if good_hours:
            st.success(f"✅ **Momenti migliori**: Condizioni ottimali alle {', '.join([h['time'] for h in good_hours])}")

    # Raccomandazioni principali
    st.markdown("---")
    st.subheader("🎯 Specie Consigliate Oggi")

    # Calcola punteggi per la zona selezionata
    fish_scores = {}
    for fish_name, fish_data in FISH_SPECIES.items():
        habitat_match = any(habitat in zona_selezionata for habitat in fish_data['habitat'])
        if habitat_match:
            score = calculate_fish_activity(fish_data, weather_data, moon_phase, current_season, zona_selezionata)
            fish_scores[fish_name] = score

    if not fish_scores:
        st.warning("⚠️ Nessuna specie trovata per questa zona. Prova un'altra località.")
    else:
        sorted_fish = sorted(fish_scores.items(), key=lambda x: x[1], reverse=True)

        cols = st.columns(3)
        for i, (fish, score) in enumerate(sorted_fish[:3]):
            with cols[i]:
                if score >= 75:
                    emoji = "🔥"
                    delta_color = "normal"
                elif score >= 60:
                    emoji = "👍"
                    delta_color = "normal"
                elif score >= 45:
                    emoji = "⚠️"
                    delta_color = "off"
                else:
                    emoji = "❄️"
                    delta_color = "inverse"
                
                st.metric(f"{emoji} {fish}", f"{score}/100", delta_color=delta_color)

    # Dettagli per ogni specie della zona
    st.markdown("---")
    st.subheader("📈 Dettaglio Specie per Zona")

    fish_list_for_zone = []
    for fish_name, fish_data in FISH_SPECIES.items():
        habitat_match = any(habitat in zona_selezionata for habitat in fish_data['habitat'])
        if habitat_match:
            score = calculate_fish_activity(fish_data, weather_data, moon_phase, current_season, zona_selezionata)
            fish_list_for_zone.append((fish_name, fish_data, score))

    fish_list_for_zone.sort(key=lambda x: x[2], reverse=True)

    for fish_name, fish_data, score in fish_list_for_zone:
        if score >= 75:
            border_color = "#00ff00"
            score_color = "green"
        elif score >= 60:
            border_color = "#ffa500"
            score_color = "orange"
        elif score >= 45:
            border_color = "#ffff00"
            score_color = "blue"
        else:
            border_color = "#ff0000"
            score_color = "red"
        
        st.markdown(f"""
        <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: {score_color};">{fish_name} - {score}/100</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            image_path = get_fish_image(fish_name)
            if image_path:
                # CORRETTO: sostituito use_container_width con width='stretch'
                st.image(image_path, caption=fish_name, width='stretch')
            else:
                st.markdown(f"""
                <div style="background: #f0f0f0; border-radius: 10px; padding: 20px; text-align: center;">
                    <p style="margin: 0; color: #666;">🎣</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">{fish_name}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col_info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🎯 Condizioni:**")
                st.write(f"🌡️ Acqua ideale: {fish_data['temp_min']}-{fish_data['temp_max']}°C")
                st.write(f"📊 Pressione: {fish_data['pressure_low']}-{fish_data['pressure_high']} hPa")
                st.write(f"🌙 Fasi lunari: {', '.join([p.split(' ')[-1] for p in fish_data['moon_best']])}")
                
            with col2:
                st.write("**🎣 Tecniche:**")
                st.write(f"⏰ Orari: {', '.join(fish_data['active_hours'])}")
                st.write(f"🪙 Esche: {', '.join(fish_data['esche'])}")
                if fish_data['zone_preferite']:
                    st.write(f"📍 Zone preferite: {', '.join(fish_data['zone_preferite'])}")
            
            st.progress(score/100)
        
        st.markdown("---")

    # Consigli generali
    st.markdown("---")
    st.subheader("💡 Consigli per Oggi")

    if fish_scores:
        general_score = np.mean(list(fish_scores.values()))
        
        if general_score >= 70:
            st.success("**🎯 OTTIMA GIORNATA!** Pesci molto attivi, condizioni perfette per pescare!")
        elif general_score >= 55:
            st.warning("**👍 BUONA GIORNATA** Condizioni favorevoli, concentrati sulle specie indicate")
        else:
            st.error("**⚠️ GIORNATA DIFFICILE** Meglio rimandare o pescare in orari specifici con tecniche passive")
    else:
        st.info("Seleziona una zona di pesca per vedere i consigli specifici")

with tab2:
    st.header("📅 Calendario Aperture Pesca - Lombardia 2025")
    st.info("🎯 **Regolamento regionale** - Verifica sempre gli aggiornamenti ufficiali")
    
    today = date.today()
    
    # Filtro per stato apertura
    stato_filtro = st.selectbox(
        "Filtra per stato:",
        ["Tutti", "🟢 APERTA", "🔴 CHIUSA"],
        key="filtro_stato"
    )
    
    st.markdown("---")
    
    for specie, info in FISHING_CALENDAR.items():
        # Determina stato attuale
        is_open = info['apertura'] <= today <= info['chiusura']
        status = "🟢 APERTA" if is_open else "🔴 CHIUSA"
        
        # Applica filtro
        if stato_filtro == "Tutti" or stato_filtro == status:
            with st.expander(f"{specie} - {status}", expanded=True):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write("**📅 Periodo di Pesca**")
                    st.write(f"**Dal:** {info['apertura'].strftime('%d/%m/%Y')}")
                    st.write(f"**Al:** {info['chiusura'].strftime('%d/%m/%Y')}")
                    
                    # Calcola giorni rimanenti o giorni passati
                    if is_open:
                        giorni_rimanenti = (info['chiusura'] - today).days
                        st.success(f"**{giorni_rimanenti} giorni rimanenti**")
                    else:
                        if today < info['apertura']:
                            giorni_attesa = (info['apertura'] - today).days
                            st.warning(f"**Apertura tra {giorni_attesa} giorni**")
                        else:
                            st.error("**Stagione conclusa**")
                
                with col2:
                    st.write("**📍 Zone Abilitate**")
                    for zona in info['zone']:
                        st.write(f"• {zona}")
                    
                    st.write("**📋 Normative**")
                    st.info(f"{info['note']}")
                    
                    # Indicatori speciali
                    if "Luccio" in specie and "Divieto" in info['note']:
                        st.warning("🚫 **Periodo di divieto:** 15 Marzo - 31 Maggio")
                    if "Siluro" in specie and "rimozione" in info['note']:
                        st.error("🗑️ **Obbligo di rimozione**")
                    if "Limite giornaliero" in info['note']:
                        limite = info['note'].split("Limite giornaliero")[1].split(" ")[1]
                        st.warning(f"🎯 **Limite giornaliero:** {limite} esemplari")
    
    # Informazioni importanti - RIORGANIZZATE
    st.markdown("---")
    st.subheader("ℹ️ Informazioni Importanti")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.info("""
        **Misure Minime:**
        
        • **Trota Fario**: 22 cm
                   
        • **Luccio**: 50 cm  
                   
        • **Persico Reale**: 18 cm
                   
        • **Cavedano**: 15 cm
                   
        • **Barbo**: 20 cm
                   
        • **Luccio Perca**: 18 cm
        """)
        
        st.error("""
        **🚫 Divieti Speciali:**
        
        • **Luccio**: Divieto di pesca dal 15/03 al 31/05
                 
        • **Siluro**: Obbligo di rimozione
                 
        • Rispetta sempre i limiti giornalieri
        """)
    
    with col_info2:
        st.info("""
        **Note Generali:**
                   
        • **Carpa**: Nessuna misura minima
                   
        • **Siluro**: Nessuna misura minima
                   
        • Porta sempre con te la licenza di pesca
                
        • Porta sempre con te il tesserino pesca
                   
        • Rispetta l'ambiente naturale
                   
        • Rispetta i pesci
        """)
    
        # pdf e link ufficiali
    st.markdown("---")
    st.markdown("### 📋 Documenti Ufficiali")

    st.info("""
        **Per il regolamento completo e aggiornamenti ufficiali:**  
        🌐 [Regione Lombardia - Pesca](https://www.regione.lombardia.it/wps/portal/istituzionale/HP/servizi-e-informazioni/Enti-e-Operatori/settore-ittico-e-pesca/regolamento-regionale-pesca)

        **Contatti utili:**
        - 📞 Numero Verde: 800.318.318  
        - 🚨 Guardia Pesca: 112
        - 📧 Email: pesca@regione.lombardia.it
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🎣 Dati meteo in tempo reale da Open-Meteo •📍 By Il Sampei di Busto Arsizio KM<br>
    ⚠️ Verifica sempre il regolamento ufficiale della Regione Lombardia
    </div>
    """,
    unsafe_allow_html=True
)
