import numpy as np
import requests
import folium
import matplotlib.cm as cm
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


def get_global_solar_points(lat_step=10, lon_step=10, progress_bar=None, progress_text=None):
    """Wrapper that iterates through grid, updates progress, and calls cached NASA fetch."""
    grid = _generate_grid(lat_step, lon_step)
    total = len(grid)
    points = []

    for i, (lat, lon) in enumerate(grid, start=1):
        val = _fetch_point_data(lat, lon)
        if not np.isnan(val):
            points.append((lat, lon, val))
        if progress_bar:
            progress_bar.progress(i / total)
        if progress_text:
            progress_text.text(f"Fetching data… ({i}/{total})")

    return points


def add_solar_points_layer(map_obj, points):
    """Add irradiance points to map with color scale."""
    vals = [p[2] for p in points if not np.isnan(p[2])]
    vmin, vmax = min(vals), max(vals)
    cmap = cm.get_cmap("YlOrRd")

    for lat, lon, val in points:
        if np.isnan(val):
            continue
        color = tuple((np.array(cmap((val - vmin) / (vmax - vmin))[:3]) * 255).astype(int))
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=color_hex,
            fill=True,
            fill_opacity=0.8,
            popup=f"GHI: {val:.1f} W/m²"
        ).add_to(map_obj)
