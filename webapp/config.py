STATE_DATA_URL = "https://opendata.ffe.de/api/od/v_opendata?id_opendata=eq.87"
DISTRICT_DATA_URL = "https://opendata.ffe.de/api/od/v_opendata?id_opendata=eq.88"

STATE_GEOJSON_URL = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/2_hoch.geo.json"
DISTRICT_GEOJSON_URL = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/4_kreise/2_hoch.geo.json"

FEDERAL_STATES = [
    'Baden-Württemberg',
    'Bayern',
    'Brandenburg',
    'Bremen',
    'Hamburg',
    'Hessen',
    'Mecklenburg-Vorpommern',
    'Niedersachsen',
    'Nordrhein-Westfalen',
    'Rheinland-Pfalz',
    'Saarland',
    'Sachsen',
    'Sachsen-Anhalt',
    'Schleswig-Holstein',
    'Thüringen'
]

STATE_GEO_VALUES = {
    "Baden-Württemberg": (48.6616, 9.3501, 8),
    "Bayern": (48.7904, 11.4979, 8),
    "Brandenburg": (52.4125, 12.5316, 8),
    "Bremen": (53.0793, 8.8017, 8),  # adjust for Bremerhaven
    "Hamburg": (53.5488, 9.9872, 8),
    "Hessen": (50.6521, 9.1624, 8),
    "Mecklenburg-Vorpommern": (53.6127, 12.4296, 8),
    "Niedersachsen": (52.6367, 9.8451, 8),
    "Nordrhein-Westfalen": (51.4332, 7.6616, 8),
    "Rheinland-Pfalz": (50.1183, 7.3090, 8),
    "Saarland": (49.3964, 7.0230, 8),
    "Sachsen": (51.1045, 13.2017, 8),
    "Sachsen-Anhalt": (51.9503, 11.6923, 8),
    "Schleswig-Holstein": (54.5250, 9.5608, 8),
    "Thüringen": (51.0110, 10.8453, 8),
    "(Deutschland)": (51.1657, 10.4515, 5)
}

BUILDING_TYPE_MAPPING = {
        1: 'One- and Two-family Houses',
        6: 'Apartment Buildings (3-6)',
        9: 'Row Houses',
        11: 'Semi-detached Houses',
        38: 'Apartment Buildings: 7 and More Apartments',
        100: 'Total'
    }

HEAT_SOURCE_MAPPING = {
        0: 'Total',
        1: 'Air',
        2: 'Ground Probe',
        3: 'Ground Collector',
        4: 'Solar-Thermal Energy and Ice Storage'
    }