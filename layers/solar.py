import numpy as np
import requests
import folium
import matplotlib.cm as cm
from folium.plugins import HeatMap
import streamlit as st

BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
PARAM = "ALLSKY_SFC_SW_DWN"


@st.cache_data(show_spinner=False)
def _fetch_point_data(lat, lon):
    """Cached low-level call to NASA POWER."""
    url = f"{BASE_URL}?parameters={PARAM}&community=RE&longitude={lon}&latitude={lat}&format=JSON"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        ghi_vals = list(data["properties"]["parameter"][PARAM].values())
        return float(np.mean(ghi_vals))
    except Exception:
        return np.nan


@st.cache_data(show_spinner=False)
def _generate_grid(lat_step, lon_step):
    """Cached generation of coordinate grid."""
    lats = np.arange(-90, 91, lat_step)
    lons = np.arange(-180, 181, lon_step)
    return [(lat, lon) for lat in lats for lon in lons]


def get_global_solar_points(lat_step=50, lon_step=50, progress_bar=None, progress_text=None, skip_factor=1):
    """
    Fetch global solar irradiance points.
    skip_factor: take every Nth coordinate to make it faster.
    """
    grid = _generate_grid(lat_step, lon_step)
    total = len(grid)
    points = []

    for i, (lat, lon) in enumerate(grid, start=1):
        # Skip most points to make it faster
        if i % skip_factor != 0:
            continue
        val = _fetch_point_data(lat, lon)
        if not np.isnan(val):
            points.append((lat, lon, val))
        if progress_bar:
            progress_bar.progress(i / total)
        if progress_text and i % 10 == 0:
            progress_text.text(f"Fetching data… ({i}/{total})")

    return points


def add_solar_points_layer(map_obj, points):
    """Add blurred solar irradiance heatmap layer."""
    vals = [p[2] for p in points if not np.isnan(p[2])]
    if not vals:
        return
    vmin, vmax = min(vals), max(vals)

    # Normalize & build heatmap data
    heat_data = []
    for lat, lon, val in points:
        if np.isnan(val):
            continue
        weight = (val - vmin) / (vmax - vmin)
        heat_data.append([lat, lon, weight])

    # Add Gaussian-blurred heatmap
    HeatMap(
        heat_data,
        min_opacity=0.3,
        max_opacity=0.9,
        radius=50,  # controls blur spread
        blur=100,    # controls softness
        gradient={
            0.0: "#333300",  # deep navy
            0.3: "#b3ad00",  # rich blue
            0.6: "#fffc33",  # mid-blue
            0.8: "#fff566",  # lighter blue
            1.0: "#fffeb3",  # pale blue-white
        },
    ).add_to(map_obj)
