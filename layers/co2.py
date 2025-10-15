import folium
import numpy as np
import matplotlib.cm as cm
import pandas_datareader.wb as wb
import pycountry
import pycountry_convert as pc

# --- Fetch latest CO₂ data (metric tons per capita) from World Bank ---
def get_country_co2_data(year=2021):
    """Fetch real CO₂ emission data (tons per capita) for each country."""
    df = wb.download(indicator="EN.ATM.CO2E.PC",
                     country=wb.get_countries()["iso2c"],
                     start=year, end=year)
    df = df.reset_index().dropna(subset=["EN.ATM.CO2E.PC"])
    df = df.rename(columns={"EN.ATM.CO2E.PC": "co2_tons_pc"})
    return df


# --- Approx country centroids (via pycountry_convert regions) ---
def get_country_coords():
    """Approximate lat/lon by region code for all countries."""
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    geolocator = Nominatim(user_agent="terraform-earth")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.2)

    coords = {}
    for country in [c.name for c in pycountry.countries]:
        try:
            loc = geocode(country)
            if loc:
                coords[country] = (loc.latitude, loc.longitude)
        except Exception:
            continue
    return coords


def add_co2_layer(map_obj, co2_df):
    """Add proportional circles for CO₂ emissions per capita."""
    CO2_COUNTS = {row["country"]: row["co2_tons_pc"] for _, row in co2_df.iterrows()}

    vals = [v for v in CO2_COUNTS.values() if v > 0]
    vmin, vmax = min(vals), max(vals)
    cmap = cm.get_cmap("YlOrRd")

    # Get centroids (cached if needed)
    COUNTRY_COORDS = get_country_coords()

    for country, val in CO2_COUNTS.items():
        if country not in COUNTRY_COORDS:
            continue
        lat, lon = COUNTRY_COORDS[country]
        color = tuple((np.array(cmap((val - vmin) / (vmax - vmin))[:3]) * 255).astype(int))
        color_hex = "#{:02x}{:02x}{:02x}".format(*color)
        radius = 5 + 25 * (val - vmin) / (vmax - vmin)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color_hex,
            fill=True,
            fill_opacity=0.7,
            popup=f"{country}: {val:.2f} tons CO₂ per capita",
        ).add_to(map_obj)
