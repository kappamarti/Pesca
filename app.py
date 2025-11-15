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

# Coordinate precise delle zone di pesca richieste
ZONE_COORDINATES = {
    'Ticino - Sesto Calende': {'lat': 45.7286, 'lon': 8.6358},
    'Lago Maggiore - Lombardia': {'lat': 45.9000, 'lon': 8.6500},
    'Lago di Varese': {'lat': 45.8167, 'lon': 8.7333},
    'Ticino - Pavia': {'lat': 45.1865, 'lon': 9.1571}
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
        # Immagine placeholder se non trova l'immagine
        return None

# Funzione per ottenere dati meteo reali da Open-Meteo (GRATUITA)
def get_real_weather_data(lat, lon, location_name):
    """Ottiene dati meteo reali da Open-Meteo - API Gratuita"""
    try:
        # API Open-Meteo - completamente gratuita
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,cloud_cover,weather_code&timezone=Europe/Rome"
        
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
        'success': True
    }
    return weather_info

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
    """Calcola temperatura acqua approssimativa basata su condizioni attuali e location"""
    base_water_temp = air_temp
    
    # Aggiustamenti basati sulle condizioni meteo
    weather_code = current_data['weather_code']
    
    if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
        base_water_temp -= 1.5  # Pioggia/temporali raffreddano l'acqua
    elif weather_code in [0, 1]:
        base_water_temp += 2.5  # Sole riscalda l'acqua
    elif weather_code in [2, 3]:
        base_water_temp += 0.5  # Nuvoloso leggero riscaldamento
    
    # Aggiustamento specifico per location
    if "Sesto Calende" in location_name or "Panperduto" in location_name:
        # Ticino a Sesto Calende - acqua più fredda per la corrente
        base_water_temp -= 2
    elif "Lago Maggiore" in location_name:
        # Lago Maggiore - acqua più profonda e fresca
        base_water_temp -= 1
    elif "Lago di Varese" in location_name:
        # Lago di Varese - acqua più calda, lago poco profondo
        base_water_temp += 1
    elif "Pavia" in location_name:
        # Ticino a Pavia - acqua più calda, fiume più lento
        base_water_temp += 0.5
    
    # Aggiustamento stagionale
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:  # Inverno
        base_water_temp = max(2, base_water_temp - 6)
    elif current_month in [6, 7, 8]:  # Estate
        base_water_temp = min(28, base_water_temp + 4)
    elif current_month in [3, 4, 5]:  # Primavera
        base_water_temp += 1
    else:  # Autunno
        base_water_temp -= 2
    
    return round(base_water_temp, 1)

def get_fallback_weather_data(location_name):
    """Dati di fallback se l'API non funziona"""
    # Dati realistici basati sulla stagione e location
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:  # Inverno
        temp = np.random.randint(0, 8)
        water_temp = max(2, temp - 2)
        weather_cond = np.random.choice(['Nuvoloso', 'Sereno', 'Nebbia'])
    elif current_month in [6, 7, 8]:  # Estate
        temp = np.random.randint(22, 32)
        water_temp = temp - 3
        weather_cond = np.random.choice(['Sereno', 'Parzialmente nuvoloso', 'Temporale'])
    else:  # Primavera/Autunno
        temp = np.random.randint(10, 20)
        water_temp = temp - 2
        weather_cond = np.random.choice(['Nuvoloso', 'Pioggia leggera', 'Sereno'])
    
    # Aggiustamento location per fallback
    if "Sesto Calende" in location_name:
        water_temp -= 1  # Più freddo per la corrente
    elif "Lago di Varese" in location_name:
        water_temp += 1  # Più caldo per lago poco profondo
    
    return {
        'location': location_name,
        'temperature': temp,
        'water_temperature': water_temp,
        'pressure': np.random.randint(1005, 1025),
        'humidity': np.random.randint(50, 85),
        'wind_speed': np.random.randint(5, 20),
        'weather_condition': weather_cond,
        'weather_main': 'Clouds',
        'clouds': np.random.randint(20, 80),
        'visibility': np.random.randint(5, 15),
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

# INTERFACCIA PRINCIPALE
st.title("🎣 Pesca Lombardia - Zone Preferite")
st.markdown("**Dati meteo reali • Previsioni pesca accurate**")

# Selezione zona
st.subheader("📍 Seleziona Zona di Pesca")
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

# Raccomandazioni principali
st.markdown("---")
st.subheader("🎯 Specie Consigliate Oggi")

# Calcola punteggi per la zona selezionata
fish_scores = {}
for fish_name, fish_data in FISH_SPECIES.items():
    # Controlla se la specie è presente in questa zona
    habitat_match = any(habitat in zona_selezionata for habitat in fish_data['habitat'])
    if habitat_match:
        score = calculate_fish_activity(fish_data, weather_data, moon_phase, current_season, zona_selezionata)
        fish_scores[fish_name] = score

if not fish_scores:
    st.warning("⚠️ Nessuna specie trovata per questa zona. Prova un'altra località.")
else:
    # Ordina e mostra top 3
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

# Dettagli per ogni specie della zona - ORDINATI PER PUNTEGGIO
st.markdown("---")
st.subheader("📈 Dettaglio Specie per Zona")

# Crea lista ordinata per punteggio
fish_list_for_zone = []
for fish_name, fish_data in FISH_SPECIES.items():
    habitat_match = any(habitat in zona_selezionata for habitat in fish_data['habitat'])
    if habitat_match:
        score = calculate_fish_activity(fish_data, weather_data, moon_phase, current_season, zona_selezionata)
        fish_list_for_zone.append((fish_name, fish_data, score))

# Ordina per punteggio (dal più alto al più basso)
fish_list_for_zone.sort(key=lambda x: x[2], reverse=True)

# Mostra le specie ordinate
for fish_name, fish_data, score in fish_list_for_zone:
    # Colore in base al punteggio
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
    
    # Crea un container con bordo colorato
    st.markdown(f"""
    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0; color: {score_color};">{fish_name} - {score}/100</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout con immagine e informazioni
    col_img, col_info = st.columns([1, 2])
    
    with col_img:
        # Immagine del pesce
        image_path = get_fish_image(fish_name)
        if image_path:
            st.image(image_path, caption=fish_name, use_container_width=True)  # CORRETTO: use_container_width
        else:
            # Se non trova l'immagine, mostra un placeholder
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
        
        # Barra del punteggio
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

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🎣 Dati meteo in tempo reale da Open-Meteo<br>
    📍 By Il Sampei di Busto Arsizio KM
    </div>
    """,
    unsafe_allow_html=True
)
