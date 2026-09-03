from __future__ import annotations

import pandas as pd
import plotly.express as px

from .data_loader import load_geodata


def build_choropleth(indicators: pd.DataFrame, indicator_col: str):
    gdf = load_geodata()
    if gdf is None or indicator_col not in indicators.columns:
        return None
    merged = gdf.merge(indicators, on="CD_BAIRRO", how="left", suffixes=("_geo", ""))
    if merged.empty:
        return None
    if "NM_BAIRRO" not in merged.columns and "NM_BAIRRO_geo" in merged.columns:
        merged["NM_BAIRRO"] = merged["NM_BAIRRO_geo"]
    if "NM_MUN" not in merged.columns and "NM_MUN_geo" in merged.columns:
        merged["NM_MUN"] = merged["NM_MUN_geo"]
    merged = merged.to_crs(epsg=4326)
    geojson = merged.__geo_interface__
    fig = px.choropleth_mapbox(
        merged,
        geojson=geojson,
        locations=merged.index,
        color=indicator_col,
        hover_name="NM_BAIRRO",
        hover_data=[col for col in ["NM_MUN", "Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"] if col in merged.columns],
        mapbox_style="carto-darkmatter",
        center={"lat": -12.8, "lon": -41.7},
        zoom=5.2,
        opacity=0.72,
        template="plotly_dark",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=660)
    return fig
