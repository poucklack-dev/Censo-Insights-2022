from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px

from .data_loader import load_geodata


def build_choropleth(indicators: pd.DataFrame, indicator_col: str):
    gdf = load_geodata()
    if gdf is None or gdf.empty or indicator_col not in indicators.columns:
        return None

    geo = gdf.copy()
    values = indicators.copy()
    if "CD_BAIRRO" not in geo.columns or "CD_BAIRRO" not in values.columns:
        return None
    geo["CD_BAIRRO"] = geo["CD_BAIRRO"].astype("string")
    values["CD_BAIRRO"] = values["CD_BAIRRO"].astype("string")
    geo = geo.dropna(subset=["CD_BAIRRO"])
    values = values.dropna(subset=["CD_BAIRRO"])
    if geo["CD_BAIRRO"].duplicated().any() or values["CD_BAIRRO"].duplicated().any():
        raise ValueError("CD_BAIRRO deve ser unico na malha e nos indicadores.")

    values[indicator_col] = pd.to_numeric(values[indicator_col], errors="coerce")
    values[indicator_col] = values[indicator_col].replace([np.inf, -np.inf], np.nan)
    values = values.dropna(subset=[indicator_col])
    merged = geo.merge(
        values,
        on="CD_BAIRRO",
        how="inner",
        suffixes=("_geo", ""),
        validate="one_to_one",
    )
    if merged.empty:
        return None
    if "NM_BAIRRO" not in merged.columns and "NM_BAIRRO_geo" in merged.columns:
        merged["NM_BAIRRO"] = merged["NM_BAIRRO_geo"]
    if "NM_MUN" not in merged.columns and "NM_MUN_geo" in merged.columns:
        merged["NM_MUN"] = merged["NM_MUN_geo"]
    merged = merged.loc[merged.geometry.notna() & ~merged.geometry.is_empty].copy()
    if merged.empty:
        return None
    merged = merged.to_crs(epsg=4326)
    merged["CD_BAIRRO"] = merged["CD_BAIRRO"].astype(str)
    geojson = merged.__geo_interface__
    features = geojson.get("features", [])
    if not features or any(
        "CD_BAIRRO" not in feature.get("properties", {}) for feature in features
    ):
        return None
    fig = px.choropleth_map(
        merged,
        geojson=geojson,
        locations="CD_BAIRRO",
        featureidkey="properties.CD_BAIRRO",
        color=indicator_col,
        hover_name="NM_BAIRRO",
        hover_data=[col for col in ["NM_MUN", "Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"] if col in merged.columns],
        map_style="carto-darkmatter",
        center={"lat": -12.8, "lon": -41.7},
        zoom=5.2,
        opacity=0.72,
        template="plotly_dark",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=660)
    return fig
