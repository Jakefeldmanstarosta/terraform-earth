import streamlit as st
import folium
import numpy as np
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

from layers.solar import get_global_solar_points, add_solar_points_layer
from layers.pipelines import PIPELINE_COUNTS, COUNTRY_COORDS, add_pipeline_layer
from layers.co2 import get_country_co2_data, add_co2_layer, get_country_coords, resolve_admin_name

# --- Load Natural Earth land mask ---
import geopandas as gpd
from shapely.geometry import Point

# --- Load land polygons (Natural Earth) ---
LAND_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
try:
    LAND = gpd.read_file(LAND_URL)
except Exception as e:
    st.warning(f"Failed to load land polygons: {e}")
    LAND = gpd.GeoDataFrame(columns=["geometry"])

def is_on_land(lat, lon):
    """Return True if coordinate is on land (using Natural Earth polygons)."""
    if LAND.empty:
        return True  # fallback to avoid breaking
    point = Point(lon, lat)
    return LAND.contains(point).any()

# --- Streamlit setup ---
st.set_page_config(layout="wide")
st.title("terraform earth.")

# --- Sidebar: layer selector ---
st.sidebar.header("Layers")
layer_choices = st.sidebar.multiselect(
    "Select layers to display:",
    ["Solar Irradiance", "Pipeline Network", "CO₂ Emissions", "Terraformer Effectiveness"],
    default=["Terraformer Effectiveness"],
)

# --- Sidebar: sliders ---
st.sidebar.header("Terraformer Weights")
solar_weight = st.sidebar.slider("Solar", 0.0, 1.0, 0.33)
pipeline_weight = st.sidebar.slider("Pipelines", 0.0, 1.0, 0.33)
co2_weight = st.sidebar.slider("CO₂", 0.0, 1.0, 0.33)

# Normalize weights
total = solar_weight + pipeline_weight + co2_weight
if total > 0:
    solar_weight /= total
    pipeline_weight /= total
    co2_weight /= total

# --- Base map setup ---
m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodb positron")

# --- Load data ---
solar_points, co2_df = None, None

if "Solar Irradiance" in layer_choices or "Terraformer Effectiveness" in layer_choices:
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    solar_points = get_global_solar_points(
        lat_step=20, lon_step=20, progress_bar=progress_bar, progress_text=progress_text
    )
    progress_bar.empty()
    progress_text.empty()
    if "Solar Irradiance" in layer_choices:
        add_solar_points_layer(m, solar_points)

if "Pipeline Network" in layer_choices:
    add_pipeline_layer(m)

if "CO₂ Emissions" in layer_choices or "Terraformer Effectiveness" in layer_choices:
    co2_df = get_country_co2_data()
    if "CO₂ Emissions" in layer_choices:
        add_co2_layer(m, co2_df)

# --- Terraformer Effectiveness Layer ---
if "Terraformer Effectiveness" in layer_choices:
    heat_points = []
    coords_dict = get_country_coords()

    # Solar points (global grid)
    if solar_points:
        solar_vals = [p[2] for p in solar_points]
        smin, smax = min(solar_vals), max(solar_vals)
        for lat, lon, val in solar_points:
            if not is_on_land(lat, lon):
                continue
            sval = (val - smin) / (smax - smin)
            heat_points.append([lat, lon, solar_weight * sval])

    # Pipelines (country centroids)
    p_vals = list(PIPELINE_COUNTS.values())
    if p_vals:
        pmax = max(p_vals)
        for c, count in PIPELINE_COUNTS.items():
            if c not in COUNTRY_COORDS:
                continue
            lat, lon = COUNTRY_COORDS[c]
            if not is_on_land(lat, lon):
                continue
            pval = count / pmax
            heat_points.append([lat, lon, pipeline_weight * pval])

    # CO₂ (country centroids)
    if co2_df is not None:
        co2_vals = co2_df["co2_total_mt"].values
        cmax = float(np.nanmax(co2_vals))
        for _, row in co2_df.iterrows():
            admin = resolve_admin_name(row["country_key"], coords_dict)
            if not admin:
                continue
            lat, lon = coords_dict[admin]
            if not is_on_land(lat, lon):
                continue
            val = float(row["co2_total_mt"])
            if not np.isfinite(val) or val <= 0:
                continue
            norm_val = val / cmax
            heat_points.append([lat, lon, co2_weight * norm_val])

    # Combine into final layer
    if heat_points:
        HeatMap(
            heat_points,
            name="Terraformer Effectiveness",
            min_opacity=0.25,
            max_opacity=0.95,
            radius=45,
            blur=90,
            gradient={
                0.0: "#FFE6F7",
                0.3: "#fbabdf",
                0.6: "#fc87ef",
                0.8: "#fb4ed2",
                1.0: "#B1078F",
            },
        ).add_to(m)
    else:
        st.warning("No data available to render Terraformer layer.")

# --- Add map controls and render ---
folium.LayerControl().add_to(m)
st_folium(m, width=1100, height=600)

st.subheader("Data Sources")
st.markdown( """ - **Solar Irradiance:** [NASA POWER API](https://power.larc.nasa.gov/data-access-viewer/) 
            \n- **Pipeline Network:** [Global Energy Monitor – Global NGL pipeline km by country](https://globalenergymonitor.org/projects/global-oil-infrastructure-tracker/) 
            \n- **CO₂ Emissions:** [World Bank Group – Carbon dioxide (CO2) emissions (total)](https://data.worldbank.org/indicator/EN.GHG.CO2.MT.CE.AR5?end=2023&name_desc=true&start=2023&view=map) """, unsafe_allow_html=True, )
