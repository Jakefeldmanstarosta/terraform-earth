import folium
import numpy as np
import matplotlib.cm as cm

#data is from https://docs.google.com/spreadsheets/d/1OYH6D7c-D0FsL5GzBGijtkmvQCTkBUclj-UVoOieUFo/edit?gid=2081466919#gid=2081466919
# from the Global Energy Monitor: https://globalenergymonitor.org/projects/global-oil-infrastructure-tracker/
PIPELINE_COUNTS = {
    "Argentina": 1709,
    "Australia": 1453,
    "Azerbaijan": 525,
    "Brazil": 1371,
    "Canada": 5343,
    "Chile": 156,
    "China": 3302,
    "Colombia": 1474,
    "Ecuador": 642,
    "France": 260,
    "Georgia": 248,
    "Germany": 43,
    "India": 4466,
    "Iran": 248,
    "Kazakhstan": 2468,
    "Libya": 595,
    "Mexico": 21,
    "Netherlands": 432,
    "New Zealand": 10,
    "Oman": 300,
    "Panama": 0,
    "Peru": 560,
    "Qatar": 437,
    "Russia": 12187,
    "Saudi Arabia": 1580,
    "Spain": 350,
    "Switzerland": 118,
    "Türkiye": 1075,
    "United Arab Emirates": 306,
    "United Kingdom": 37,
    "United States": 51123,
}

# Approximate country centroids (lat, lon)
COUNTRY_COORDS = {
    "Argentina": (-38.4, -63.6),
    "Australia": (-25.3, 133.8),
    "Azerbaijan": (40.1, 47.6),
    "Brazil": (-10.8, -52.9),
    "Canada": (56.1, -106.3),
    "Chile": (-35.7, -71.5),
    "China": (35.9, 104.2),
    "Colombia": (4.6, -74.1),
    "Ecuador": (-1.8, -78.2),
    "France": (46.2, 2.2),
    "Georgia": (42.3, 43.4),
    "Germany": (51.2, 10.5),
    "India": (20.6, 78.9),
    "Iran": (32.4, 53.7),
    "Kazakhstan": (48.0, 67.0),
    "Libya": (26.3, 17.2),
    "Mexico": (23.6, -102.6),
    "Netherlands": (52.1, 5.3),
    "New Zealand": (-40.9, 174.9),
    "Oman": (21.5, 55.9),
    "Panama": (8.5, -80.8),
    "Peru": (-9.2, -75.0),
    "Qatar": (25.3, 51.2),
    "Russia": (61.5, 105.3),
    "Saudi Arabia": (23.9, 45.1),
    "Spain": (40.5, -3.7),
    "Switzerland": (46.8, 8.2),
    "Türkiye": (39.0, 35.2),
    "United Arab Emirates": (23.4, 53.8),
    "United Kingdom": (55.4, -3.4),
    "United States": (37.1, -95.7),
}

def add_pipeline_layer(map_obj):
    """Add proportional circles for number of operating pipelines per country."""
    vals = [v for v in PIPELINE_COUNTS.values() if v > 0]
    vmin, vmax = min(vals), max(vals)
    cmap = cm.get_cmap("Blues")

    for country, count in PIPELINE_COUNTS.items():
        if count == 0 or country not in COUNTRY_COORDS:
            continue
        lat, lon = COUNTRY_COORDS[country]
        color = tuple((np.array(cmap((count - vmin) / (vmax - vmin))[:3]) * 255).astype(int))
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        radius = 5 + 25 * (count - vmin) / (vmax - vmin)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color_hex,
            fill=True,
            fill_opacity=0.7,
            popup=f"{country}: {count:,}km of pipelines",
        ).add_to(map_obj)
