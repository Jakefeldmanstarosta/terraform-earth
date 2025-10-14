# terraform_map.py
import streamlit as st
import folium
import numpy as np
import rasterio
from rasterio.enums import Resampling
from branca.colormap import linear
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Terraform Suitability Map")

st.title("🌍 Terraform Industries — Solar + CO₂ Suitability Map")

st.markdown("""
This map overlays two core environmental factors for Terraform Industries:
- **Solar irradiance** (energy input)
- **Atmospheric CO₂ concentration** (feedstock availability)
""")

# Sidebar controls
st.sidebar.header("Adjust Weights")
solar_w = st.sidebar.slider("Solar Weight", 0.0, 1.0, 0.6, 0.05)
co2_w = 1 - solar_w
st.sidebar.markdown(f"CO₂ Weight = **{co2_w:.2f}**")

# --- Load example rasters (replace with NASA / CAMS files) ---
# For demo purposes, we create synthetic arrays
width, height = 180, 90
lon = np.linspace(-180, 180, width)
lat = np.linspace(-90, 90, height)
lon_grid, lat_grid = np.meshgrid(lon, lat)

# Synthetic solar irradiance (more near equator)
solar_data = np.clip(np.cos(np.radians(lat_grid)) + 0.1 * np.random.randn(*lat_grid.shape), 0, 1)

# Synthetic CO2 (higher near industrial zones: northern midlatitudes)
co2_data = np.clip(0.6 - 0.004 * np.abs(lat_grid - 40) + 0.05 * np.random.randn(*lat_grid.shape), 0, 1)

# Combine layers by weights
suitability = solar_w * solar_data + co2_w * co2_data

# --- Build Folium map ---
m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodb positron")

# Add Solar Layer
solar_colormap = linear.YlOrRd_09.scale(0, 1)
folium.raster_layers.ImageOverlay(
    name="Solar Irradiance",
    image=solar_data,
    bounds=[[-90, -180], [90, 180]],
    opacity=0.7,
    colormap=lambda x: solar_colormap(x),
).add_to(m)

# Add CO2 Layer
co2_colormap = linear.Blues_09.scale(0, 1)
folium.raster_layers.ImageOverlay(
    name="CO₂ Concentration",
    image=co2_data,
    bounds=[[-90, -180], [90, 180]],
    opacity=0.7,
    colormap=lambda x: co2_colormap(x),
).add_to(m)

# Add Suitability Layer
suit_colormap = linear.Viridis_09.scale(0, 1)
folium.raster_layers.ImageOverlay(
    name="Composite Suitability",
    image=suitability,
    bounds=[[-90, -180], [90, 180]],
    opacity=0.7,
    colormap=lambda x: suit_colormap(x),
).add_to(m)

# Add controls
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=1200, height=650)
