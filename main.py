import streamlit as st
import folium
from streamlit_folium import st_folium
from layers.solar import get_global_solar_points, add_solar_points_layer
from layers.pipelines import add_pipeline_layer
from layers.co2 import get_country_co2_data, add_co2_layer


st.set_page_config(layout="wide")
st.title("terraform earth.")

# --- Sidebar / Layer selector ---
st.sidebar.header("🌍 Layers")
layer_choices = st.sidebar.multiselect(
    "Select layers to display:",
    ["Solar Irradiance", "Pipeline Network", "CO₂ Emissions"],
    default=["Solar Irradiance"],
)

# --- Base map setup ---
m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodb positron")

# --- Solar layer ---
if "Solar Irradiance" in layer_choices:
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    st.info("Fetching (cached) NASA POWER solar data…")

    points = get_global_solar_points(
        lat_step=20,
        lon_step=20,
        progress_bar=progress_bar,
        progress_text=progress_text,
    )

    progress_text.text("Rendering solar layer…")
    add_solar_points_layer(m, points)

    progress_bar.empty()
    progress_text.empty()
    st.success("✅ Solar layer loaded.")

# --- Pipeline layer ---
if "Pipeline Network" in layer_choices:
    add_pipeline_layer(m)
    st.success("✅ Pipeline layer loaded.")

if "CO₂ Emissions" in layer_choices:
    st.info("Fetching CO₂ data from World Bank API…")
    co2_df = get_country_co2_data()
    add_co2_layer(m, co2_df)
    st.success("✅ CO₂ emissions layer loaded.")

# --- Add base controls and render ---
folium.LayerControl().add_to(m)
st_folium(m, width=1100, height=600)
