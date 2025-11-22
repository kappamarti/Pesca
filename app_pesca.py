import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import requests
import json
import os
import pickle
from database_pesca import ZONE_COORDINATES, FISHING_CALENDAR, FISH_SPECIES

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

# File per salvare le temperature storiche
WATER_TEMP_HISTORY_FILE = "water_temp_history.pkl"

def load_water_temp_history():
    """Carica lo storico delle temperature dell'acqua"""
    try:
        if os.path.exists(WATER_TEMP_HISTORY_FILE):
            with open(WATER_TEMP_HISTORY_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return {}

def save_water_temp_history(history):
    """Salva lo storico delle temperature dell'acqua"""
    try:
        with open(WATER_TEMP_HISTORY_FILE, 'wb') as f:
            pickle.dump(history, f)
    except:
        pass

def get_water_level_trend(location_name, current_data):
    """Determina l'andamento del livello dell'acqua basato su meteo e condizioni"""
    precipitation = current_data.get('precipitation', 0)
    weather_code = current_data.get('weather_code', 0)
    
    # Pioggia attuale o prevista aumenta il livello
    if weather_code in [61, 63, 65, 80, 81, 82, 95, 96, 99]:
        return "↑ Salendo", "green"
    elif precipitation > 2.0:
        return "↑ Salendo", "green"
    # Condizioni secche diminuiscono il livello
    elif weather_code in [0, 1] and precipitation == 0:
        return "↓ Scendendo", "red"
    else:
        return "→ Stabile", "blue"

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

def calculate_water_temperature(air_temp, current_data, location_name):
    """Calcola temperatura acqua considerando l'assorbimento termico dell'acqua"""
    
    current_date = datetime.now().date()
    current_month = datetime.now().month
    current_hour = datetime.now().hour
    
    # Carica storico temperature
    temp_history = load_water_temp_history()
    
    # Dati REALI temperatura acqua medi per zona (basati su dati ARPA)
    water_data = {
        # Mese: Panperduto, Lago Maggiore, Lago di Varese, Oleggio
        1: {'Panperduto': 6.5, 'Lago Maggiore - Lombardia': 6.0, 'Lago di Varese': 5.0, 'Oleggio': 6.0},
        2: {'Panperduto': 7.0, 'Lago Maggiore - Lombardia': 6.5, 'Lago di Varese': 5.5, 'Oleggio': 6.5},
        3: {'Panperduto': 9.0, 'Lago Maggiore - Lombardia': 8.0, 'Lago di Varese': 7.5, 'Oleggio': 8.5},
        4: {'Panperduto': 12.0, 'Lago Maggiore - Lombardia': 10.5, 'Lago di Varese': 12.0, 'Oleggio': 11.5},
        5: {'Panperduto': 16.0, 'Lago Maggiore - Lombardia': 14.0, 'Lago di Varese': 17.0, 'Oleggio': 15.5},
        6: {'Panperduto': 19.0, 'Lago Maggiore - Lombardia': 18.0, 'Lago di Varese': 21.0, 'Oleggio': 18.5},
        7: {'Panperduto': 21.0, 'Lago Maggiore - Lombardia': 21.5, 'Lago di Varese': 24.0, 'Oleggio': 20.5},
        8: {'Panperduto': 20.5, 'Lago Maggiore - Lombardia': 22.0, 'Lago di Varese': 23.5, 'Oleggio': 20.0},
        9: {'Panperduto': 18.0, 'Lago Maggiore - Lombardia': 19.0, 'Lago di Varese': 20.0, 'Oleggio': 17.5},
        10: {'Panperduto': 14.5, 'Lago Maggiore - Lombardia': 15.0, 'Lago di Varese': 15.5, 'Oleggio': 14.0},
        11: {'Panperduto': 10.5, 'Lago Maggiore - Lombardia': 11.0, 'Lago di Varese': 10.0, 'Oleggio': 10.0},
        12: {'Panperduto': 7.5, 'Lago Maggiore - Lombardia': 7.0, 'Lago di Varese': 6.0, 'Oleggio': 7.0}
    }
    
    # Temperatura base stagionale per la zona
    seasonal_base = water_data[current_month].get(location_name, 15.0)
    
    # Recupera temperatura precedente (se esiste)
    location_key = f"{location_name}_{current_month}"
    previous_temp = None
    heat_accumulation = 0
    
    if location_key in temp_history:
        history_data = temp_history[location_key]
        previous_temp = history_data['temp']
        heat_accumulation = history_data.get('heat_accumulation', 0)
        last_date = history_data['date']
        
        # Calcola giorni passati dall'ultimo aggiornamento
        days_passed = (current_date - last_date).days
    else:
        days_passed = 1
        previous_temp = seasonal_base
    
    # 1. ASSORBIMENTO TERMICO - L'acqua accumula calore lentamente
    current_air_temp = air_temp
    
    # Differenza tra aria e acqua - questo è il POTENZIALE di scambio termico
    temp_gap = current_air_temp - previous_temp
    
    # Coefficiente di assorbimento (molto basso - l'acqua assorbe lentamente)
    absorption_rate = 0.08  # Solo l'8% del gap termico viene assorbito giornalemente
    
    # Se l'aria è più calda dell'acqua, l'acqua ASSORBE calore
    if temp_gap > 0:
        daily_heat_gain = temp_gap * absorption_rate
        # L'assorbimento è maggiore di giorno e con sole
        if 8 <= current_hour <= 18:  # Ore diurne
            daily_heat_gain *= 1.3
        if current_data['weather_code'] in [0, 1]:  # Cielo sereno
            daily_heat_gain *= 1.5
    else:
        # Se l'aria è più fredda, l'acqua PERDE calore (più lentamente)
        daily_heat_gain = temp_gap * (absorption_rate * 0.6)  # Perde calore più lentamente
    
    # 2. ACCUMULO TERMICO - L'acqua ha una "memoria" del calore assorbito
    heat_accumulation += daily_heat_gain
    
    # L'accumulo si dissipa lentamente nel tempo (effetto di rilascio)
    heat_dissipation = heat_accumulation * 0.05  # 5% di dissipazione giornaliera
    heat_accumulation -= heat_dissipation
    
    # Limita l'accumulo per evitare valori estremi
    max_heat_accumulation = 8.0  # Massimo accumulo possibile
    heat_accumulation = max(-max_heat_accumulation, min(max_heat_accumulation, heat_accumulation))
    
    # 3. CALCOLO TEMPERATURA CON ASSORBIMENTO
    water_temp = previous_temp + heat_accumulation
    
    # 4. EFFETTI IMMEDIATI (limitati)
    immediate_effects = 0
    
    # Pioggia raffredda immediatamente lo strato superficiale
    if current_data['weather_code'] in [61, 63, 65, 80, 81, 82]:
        immediate_effects -= 0.3
    
    # Vento forte aumenta lo scambio termico superficiale
    wind_speed = current_data.get('wind_speed_10m', 0) * 3.6
    if wind_speed > 25:
        if current_air_temp < water_temp:
            immediate_effects -= 0.4  # Raffreddamento da vento
        else:
            immediate_effects += 0.2  # Riscaldamento da vento
    
    # 5. CARATTERISTICHE SPECIFICHE DELLA ZONA
    zone_modifier = 0
    
    if "Panperduto" in location_name:
        # Fiume - assorbe e perde calore più velocemente
        zone_modifier = heat_accumulation * 1.2
    
    elif "Lago Maggiore" in location_name:
        # Grande lago - altissima inerzia termica
        zone_modifier = heat_accumulation * 0.7
    
    elif "Lago di Varese" in location_name:
        # Lago piccolo - si scalda più velocemente
        zone_modifier = heat_accumulation * 1.4
    
    elif "Oleggio" in location_name:
        # Fiume Ticino - caratteristiche intermedie
        zone_modifier = heat_accumulation * 1.1
    
    # 6. APPLICA TUTTI GLI EFFETTI
    water_temp = water_temp + immediate_effects + zone_modifier
    
    # 7. MANTIENI UNA BASE STAGIONALE (l'acqua non può scostarsi troppo dalla media stagionale)
    seasonal_attraction = (seasonal_base - water_temp) * 0.1  # Tende verso la media stagionale
    water_temp += seasonal_attraction
    
    # 8. LIMITI REALISTICI
    limits = {
        'Panperduto': (4, 24),
        'Lago Maggiore - Lombardia': (5, 25),
        'Lago di Varese': (4, 26),
        'Oleggio': (4, 23)
    }
    
    min_temp, max_temp = limits.get(location_name, (2, 28))
    water_temp = max(min_temp, min(max_temp, water_temp))
    
    # 9. SALVA LO STATO TERMICO
    temp_history[location_key] = {
        'temp': water_temp,
        'date': current_date,
        'heat_accumulation': heat_accumulation,
        'air_temp': current_air_temp,
        'seasonal_base': seasonal_base
    }
    
    # Pulizia storico vecchio
    keys_to_remove = []
    for key, data in temp_history.items():
        if (current_date - data['date']).days > 30:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del temp_history[key]
    
    save_water_temp_history(temp_history)
    
    # 10. ARROTONDAMENTO FINALE
    water_temp = round(water_temp, 1)
    
    return water_temp

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
    
    # Calcola andamento livello acqua
    water_level_trend, level_color = get_water_level_trend(location_name, current)
    
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
        'water_level_trend': water_level_trend,
        'water_level_color': level_color,
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
    
    if "Panperduto" in location_name:
        water_temp -= 1
    elif "Lago di Varese" in location_name:
        water_temp += 1
    elif "Oleggio" in location_name:
        water_temp += 0.5
    
    # Calcola andamento livello acqua per fallback
    water_level_trend, level_color = get_water_level_trend(location_name, {'weather_code': 0})
    
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
        'water_level_trend': water_level_trend,
        'water_level_color': level_color,
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

# NAVIGAZIONE CON 2 TAB SEPARATI
st.title("🎣 Pesca Lombardia")

# Creiamo 2 tab separati
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Temperatura Aria", f"{weather_data['temperature']}°C")
        st.metric("Umidità", f"{weather_data['humidity']}%")

    with col2:
        st.metric("Temperatura Acqua", f"{weather_data['water_temperature']}°C")
        st.metric("Vento", f"{weather_data['wind_speed']} km/h")

    with col3:
        st.metric("Pressione", f"{weather_data['pressure']} hPa")
        st.metric("Nuvolosità", f"{weather_data['clouds']}%")
        
    with col4:
        # Mostra livello acqua con freccia colorata
        level_emoji = "🌊"
        if "↑" in weather_data['water_level_trend']:
            level_emoji = "📈"
        elif "↓" in weather_data['water_level_trend']:
            level_emoji = "📉"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-radius: 10px; background: {weather_data['water_level_color']}20; border: 1px solid {weather_data['water_level_color']}50;">
            <h3 style="margin: 0; color: {weather_data['water_level_color']};">{level_emoji} {weather_data['water_level_trend']}</h3>
            <p style="margin: 0; font-size: 0.9em; color: #666;">Livello acqua</p>
        </div>
        """, unsafe_allow_html=True)

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

    # PREVISIONI ORARIE - SOLO STREAMLIT
    st.markdown("---")
    st.subheader("⏰ Previsioni Prossime 6 Ore")

    if 'hourly_forecast' in weather_data and weather_data['hourly_forecast']:
        forecast_data = weather_data['hourly_forecast']
        
        # Crea le cards centrate
        cols = st.columns(len(forecast_data))
        
        for i, (col, hour_data) in enumerate(zip(cols, forecast_data)):
            with col:
                # Determina emoji
                hour = int(hour_data['time'].split(':')[0])
                is_night = hour >= 20 or hour <= 6
                
                if "Pioggia" in hour_data['weather_description'] or "Rovesci" in hour_data['weather_description']:
                    emoji = "🌧️"
                elif "Temporale" in hour_data['weather_description']:
                    emoji = "⛈️"
                elif "Nuvoloso" in hour_data['weather_description']:
                    emoji = "☁️"
                elif "Nebbia" in hour_data['weather_description']:
                    emoji = "🌫️"
                elif "Sereno" in hour_data['weather_description']:
                    emoji = "🌙" if is_night else "☀️"
                else:
                    emoji = "⛅"
                
                # Card con st.container()
                with st.container():
                    st.markdown(f"### {emoji}")
                    st.markdown(f"**{hour_data['time']}**")
                    st.markdown(f"**{hour_data['temperature']}°C**")
                    st.markdown(f"{hour_data['weather_description']}")
                    st.markdown(f"📊 {hour_data['pressure']} hPa")
                    
                    if hour_data['precipitation_probability'] > 20:
                        st.markdown(f"💧 {hour_data['precipitation_probability']}%")
                    
                    st.markdown(f"🌬️ {hour_data['wind_speed']} km/h")
                
                # Aggiungi un po' di spazio tra le cards
                st.markdown("<br>", unsafe_allow_html=True)

        # Analizza le previsioni
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
    
    # Informazioni importanti
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
