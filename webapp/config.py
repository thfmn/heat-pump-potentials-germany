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

DISTRICT_DATA_SELECTION = {
    'Baden-Württemberg': 'bw_full_data.csv',
    'Bayern': 'by_full_data.csv',
    'Brandenburg': 'bb_full_data.csv',
    'Bremen': 'hb_full_data.csv',
    'Hamburg': 'hh_full_data.csv',
    'Hessen': 'he_full_data.csv',
    'Mecklenburg-Vorpommern': 'mv_full_data.csv',
    'Niedersachsen': 'ni_full_data.csv',
    'Nordrhein-Westfalen': 'nw_full_data.csv',
    'Rheinland-Pfalz': 'rp_full_data.csv',
    'Saarland': 'sl_full_data.csv',
    'Sachsen': 'sn_full_data.csv',
    'Sachsen-Anhalt': 'st_full_data.csv',
    'Schleswig-Holstein': 'sh_full_data.csv',
    'Thüringen': 'th_full_data.csv'
}

STATE_GEO_VALUES = {
    "Baden-Württemberg": (48.6, 9.1, 6.85),
    "Bayern": (48.90, 11.45, 6.3),
    "Brandenburg": (52.45, 13.1, 6.8),
    "Bremen": (53.3, 8.6, 8.6),
    "Hamburg": (53.55, 10, 9),
    "Hessen": (50.6521, 9.1624, 6.7),
    "Mecklenburg-Vorpommern": (53.67, 12.43, 7),
    "Niedersachsen": (52.64, 9.85, 7),
    "Nordrhein-Westfalen": (51.4332, 7.6616, 6.8),
    "Rheinland-Pfalz": (49.8, 7.3, 7.0),
    "Saarland": (49.3964, 6.9, 8.3),
    "Sachsen": (51.1045, 13.2017, 8),
    "Sachsen-Anhalt": (51.9503, 11.6923, 8),
    "Schleswig-Holstein": (54.15, 9.8, 7.0),
    "Thüringen": (50.8, 11.25, 7.3),
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
