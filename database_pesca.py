# Database delle specie ittiche e configurazioni

from datetime import date

# Coordinate precise delle zone di pesca richieste - AGGIORNATE
ZONE_COORDINATES = {
    'Panperduto': {'lat': 45.7286, 'lon': 8.6358},
    'Lago Maggiore - Lombardia': {'lat': 45.9000, 'lon': 8.6500},
    'Lago di Varese': {'lat': 45.8167, 'lon': 8.7333},
    'Oleggio': {'lat': 45.5967, 'lon': 8.6386}
}

# Calendario aperture pesca in Lombardia (Regolamento Regionale) - AGGIORNATO 2025
FISHING_CALENDAR = {
    'Trota Fario': {
        'apertura': date(2025, 3, 1),
        'chiusura': date(2025, 9, 30),
        'note': 'Misura minima 22 cm - Limite giornaliero 5 esemplari',
        'zone': ['Panperduto', 'Oleggio']
    },
    'Luccio': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 50 cm - Divieto di pesca dal 15/03 al 31/05',
        'zone': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Panperduto', 'Oleggio']
    },
    'Carpa': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Nessuna misura minima - No limite giornaliero',
        'zone': ['Lago di Varese', 'Oleggio', 'Lago Maggiore - Lombardia']
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
        'zone': ['Panperduto', 'Oleggio']
    },
    'Cavedano': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 15 cm - Limite giornaliero 20 esemplari',
        'zone': ['Panperduto', 'Oleggio']
    },
    'Luccio Perca': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 18 cm - Limite giornaliero 10 esemplari',
        'zone': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Oleggio']
    },
    'Barbo': {
        'apertura': date(2025, 1, 1),
        'chiusura': date(2025, 12, 31),
        'note': 'Misura minima 20 cm - Limite giornaliero 5 esemplari',
        'zone': ['Panperduto', 'Oleggio']
    }
}

# Database delle specie ittiche specifiche per le tue zone - AGGIORNATO CORRETTAMENTE
FISH_SPECIES = {
    'Trota Fario': {
        'temp_min': 8,
        'temp_max': 18,
        'pressure_low': 1000,
        'pressure_high': 1020,
        'moon_best': ['🌑 Luna Nuova', '🌕 Luna Piena'],
        'season_best': ['Primavera', 'Autunno'],
        'active_hours': ['mattina', 'sera'],
        'habitat': ['Panperduto', 'Oleggio'],
        'esche': ['Camoscio', 'Lombrico', 'Artificiali'],
        'tecniche': ['Spinning', 'Mosca'],
        'zone_preferite': ['Panperduto']
    },
    'Luccio': {
        'temp_min': 10,
        'temp_max': 22,
        'pressure_low': 1005,
        'pressure_high': 1025,
        'moon_best': ['🌒 Luna Crescente', '🌓 Primo Quarto'],
        'season_best': ['Primavera', 'Autunno'],
        'active_hours': ['alba', 'tramonto'],
        'habitat': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Panperduto', 'Oleggio'],
        'esche': ['Cucchiaini', 'Siluri', 'Esche vive'],
        'tecniche': ['Spinning', 'Traina'],
        'zone_preferite': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Oleggio']
    },
    'Carpa': {
        'temp_min': 15,
        'temp_max': 25,
        'pressure_low': 1010,
        'pressure_high': 1030,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Estate', 'Primavera'],
        'active_hours': ['giorno', 'sera', 'notte'],
        'habitat': ['Lago di Varese', 'Oleggio', 'Panperduto'],
        'esche': ['Mais', 'Bolle', 'Paste'],
        'tecniche': ['Carpfishing', 'Feeder'],
        'zone_preferite': ['Lago di Varese', 'Oleggio']
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
        'habitat': ['Panperduto', 'Oleggio'],
        'esche': ['Esche vive', 'Pesci morti'],
        'tecniche': ['Spinning', 'Traina', 'Fondo'],
        'zone_preferite': ['Panperduto', 'Oleggio']
    },
    'Cavedano': {
        'temp_min': 10,
        'temp_max': 26,
        'pressure_low': 1005,
        'pressure_high': 1025,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Primavera', 'Estate'],
        'active_hours': ['giorno', 'tramonto'],
        'habitat': ['Panperduto', 'Oleggio'],
        'esche': ['Lombrico', 'Mais', 'Paste'],
        'tecniche': ['Bolognese', 'Inglese'],
        'zone_preferite': ['Oleggio', 'Panperduto']
    },
    'Luccio Perca': {
        'temp_min': 14,
        'temp_max': 26,
        'pressure_low': 1008,
        'pressure_high': 1025,
        'moon_best': ['🌒 Luna Crescente', '🌓 Primo Quarto'],
        'season_best': ['Primavera', 'Estate', 'Autunno'],
        'active_hours': ['mattina', 'pomeriggio', 'sera'],
        'habitat': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Oleggio'],
        'esche': ['Cucchiaini', 'Artificiali', 'Esche vive'],
        'tecniche': ['Spinning', 'Traina', 'Bolognese'],
        'zone_preferite': ['Lago Maggiore - Lombardia', 'Lago di Varese', 'Oleggio']
    },
    'Barbo': {
        'temp_min': 12,
        'temp_max': 24,
        'pressure_low': 1005,
        'pressure_high': 1020,
        'moon_best': ['🌕 Luna Piena', '🌒 Luna Crescente'],
        'season_best': ['Primavera', 'Estate'],
        'active_hours': ['sera', 'notte'],
        'habitat': ['Panperduto', 'Oleggio'],
        'esche': ['Lombrico', 'Bigattini', 'Paste', 'Mais'],
        'tecniche': ['Bolognese', 'Feeder', 'Fondo'],
        'zone_preferite': ['Panperduto', 'Oleggio']
    }
}