# layers/co2.py
import folium
import numpy as np
import pandas as pd
import os
import json
import urllib.request
from folium.plugins import HeatMap

# --- Load CO₂ data from CSV ---
def get_country_co2_data():
    """Load hardcoded 2023 CO₂ emission data (Mt CO₂)."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    data_path = os.path.join(data_dir, "co2_2023.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Missing data file: {data_path}")
    df = pd.read_csv(data_path, quotechar='"', engine="python", on_bad_lines="skip")
    df = df.dropna(subset=["co2_total_mt"])
    # normalize country key for alias mapping
    df["country_key"] = df["country"].str.strip()
    return df


# --- Country coordinates cache (Natural Earth) ---
COORDS_FILE = os.path.join(os.path.dirname(__file__), "country_coords_ne.json")
NE_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

def _poly_mean(coords):
    arr = np.array(coords, dtype=float)
    lon, lat = np.mean(arr, axis=0)
    return float(lat), float(lon)

def _largest_outer_ring(multipoly):
    best = []
    best_len = -1
    for poly in multipoly:
        outer = poly[0] if poly and isinstance(poly[0], list) else []
        if len(outer) > best_len:
            best_len = len(outer)
            best = outer
    return best

def generate_country_coords():
    with urllib.request.urlopen(NE_URL) as resp:
        geo = json.load(resp)

    coords = {}
    for f in geo["features"]:
        props = f.get("properties", {})
        admin = props.get("ADMIN") or props.get("name") or props.get("admin")
        geom = f.get("geometry", {})
        gtype = geom.get("type")
        gcoords = geom.get("coordinates")
        if not admin or not gtype or gcoords is None:
            continue
        try:
            if gtype == "Polygon":
                lat, lon = _poly_mean(gcoords[0])
            elif gtype == "MultiPolygon":
                outer = _largest_outer_ring(gcoords)
                if not outer:
                    continue
                lat, lon = _poly_mean(outer)
            else:
                continue
            coords[admin] = (lat, lon)
        except Exception:
            continue

    with open(COORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f)
    return coords

def get_country_coords():
    if os.path.exists(COORDS_FILE):
        with open(COORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return generate_country_coords()


# --- Common WB-name → Natural Earth ADMIN aliases (enough to cover your CSV) ---
ALIASES = {
    "United States": "United States of America",
    "Russia": "Russian Federation",
    "Russian Federation": "Russian Federation",
    "Viet Nam": "Vietnam",
    "Korea, Rep.": "South Korea",
    "Korea, Dem. People's Rep.": "North Korea",
    "Congo, Dem. Rep.": "Democratic Republic of the Congo",
    "Congo, Rep.": "Republic of the Congo",
    "Gambia, The": "The Gambia",
    "Bahamas, The": "The Bahamas",
    "Egypt, Arab Rep.": "Egypt",
    "Iran, Islamic Rep.": "Iran",
    "Hong Kong SAR, China": "Hong Kong S.A.R. of China",
    "Macao SAR, China": "Macao S.A.R, China",
    "Cote d'Ivoire": "Côte d’Ivoire",
    "Czechia": "Czech Republic",
    "Turkiye": "Turkey",
    "Syrian Arab Republic": "Syria",
    "Lao PDR": "Laos",
    "Kyrgyz Republic": "Kyrgyzstan",
    "Micronesia, Fed. Sts.": "Federated States of Micronesia",
    "Yemen, Rep.": "Yemen",
    "Venezuela, RB": "Venezuela",
    "Brunei Darussalam": "Brunei",
    "Eswatini": "Swaziland",
    "North Macedonia": "Macedonia",
    "Myanmar": "Myanmar",
    "Cabo Verde": "Cape Verde",
    "Timor-Leste": "East Timor",
    "São Tomé and Príncipe": "Sao Tome and Principe",  # guard both ways
    "Sao Tome and Principe": "Sao Tome and Principe",
    "Palestine": "Palestine",
    "West Bank and Gaza": "Palestine",
    "Curacao": "Curaçao",
    "Sint Maarten (Dutch part)": "Sint Maarten",
    "Channel Islands": "Jersey",  # there’s no single polygon; pick one to avoid crash
    "Virgin Islands (U.S.)": "United States Virgin Islands",
    "Puerto Rico (US)": "Puerto Rico",
    "French Polynesia": "French Polynesia",
    "Greenland": "Greenland",
}

def resolve_admin_name(name, coords_dict):
    # Exact
    if name in coords_dict:
        return name
    # Alias
    alias = ALIASES.get(name)
    if alias and alias in coords_dict:
        return alias
    # Try minor punctuation/diacritics fixes
    cand = name.replace("’", "'")
    if cand in coords_dict:
        return cand
    return None


# --- Folium blurred (heatmap-style) layer ---
def add_co2_layer(map_obj, co2_df):
    """
    Render CO₂ intensity as a Gaussian-blurred heatmap, weighted by *raw* Mt values.
    Uses Natural Earth centroids and a robust alias map so USA/China/etc show up.
    """
    coords = get_country_coords()

    rows = []
    for _, r in co2_df.iterrows():
        admin = resolve_admin_name(r["country_key"], coords)
        if not admin:
            continue
        lat, lon = coords[admin]
        val = float(r["co2_total_mt"])
        if not np.isfinite(val) or val <= 0:
            continue
        rows.append([lat, lon, val])

    if not rows:
        return

    rows = np.array(rows, dtype=float)
    weights = rows[:, 2]
    max_val = float(weights.max())

    # HeatMap sums weights of overlapping kernels; we pass raw Mt and set max_val
    HeatMap(
        rows.tolist(),
        min_opacity=0.25,
        max_opacity=0.95,
        radius=50,         # smaller radius to reduce “Europe pile-up”
        blur=100,
        gradient={
            0.0: "#001233",  # deep navy
            0.3: "#0056b3",  # rich blue
            0.6: "#339cff",  # mid-blue
            0.8: "#66c2ff",  # lighter blue
            1.0: "#b3e6ff",  # pale blue-white
        },
    ).add_to(map_obj)
