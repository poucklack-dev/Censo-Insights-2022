from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px

from .data_loader import load_geodata, load_neighborhood_points
from .presentation import DISPLAY_NAMES
from .utils import br_number, br_percent


FORMATTED_HOVER_COLUMNS = {
    "Populacao": lambda value: br_number(value),
    "IDR": lambda value: br_number(value, 2),
    "Representatividade feminina": br_percent,
    "Jovens": br_percent,
    "Idosos": br_percent,
}


def _formatted_hover_data(frame: pd.DataFrame):
    result = frame.copy()
    hover_data = {
        column: True
        for column in ("NM_MUN", "NM_UF")
        if column in result.columns
    }
    labels = {}
    for column, formatter in FORMATTED_HOVER_COLUMNS.items():
        if column not in result.columns:
            continue
        formatted_column = f"{column}_exibicao"
        result[formatted_column] = result[column].map(formatter)
        hover_data[column] = False
        hover_data[formatted_column] = True
        labels[formatted_column] = DISPLAY_NAMES[column]
    return result, hover_data, labels


def _prepare_values(indicators: pd.DataFrame, indicator_col: str) -> pd.DataFrame | None:
    if indicator_col not in indicators.columns or "CD_BAIRRO" not in indicators.columns:
        return None
    values = indicators.copy()
    values["CD_BAIRRO"] = values["CD_BAIRRO"].astype("string")
    values = values.dropna(subset=["CD_BAIRRO"])
    if values["CD_BAIRRO"].duplicated().any():
        raise ValueError("CD_BAIRRO deve ser unico nos indicadores.")
    values[indicator_col] = pd.to_numeric(values[indicator_col], errors="coerce")
    values[indicator_col] = values[indicator_col].replace([np.inf, -np.inf], np.nan)
    return values.dropna(subset=[indicator_col])


def build_point_map(indicators: pd.DataFrame, indicator_col: str):
    points = load_neighborhood_points()
    values = _prepare_values(indicators, indicator_col)
    if points is None or points.empty or values is None or values.empty:
        return None
    coordinates = points.copy()
    coordinates["CD_BAIRRO"] = coordinates["CD_BAIRRO"].astype("string")
    if coordinates["CD_BAIRRO"].duplicated().any():
        raise ValueError("CD_BAIRRO deve ser unico nas coordenadas.")
    merged = coordinates.merge(values, on="CD_BAIRRO", how="inner", validate="one_to_one")
    merged["LATITUDE"] = pd.to_numeric(merged["LATITUDE"], errors="coerce")
    merged["LONGITUDE"] = pd.to_numeric(merged["LONGITUDE"], errors="coerce")
    merged[["LATITUDE", "LONGITUDE"]] = merged[["LATITUDE", "LONGITUDE"]].replace(
        [np.inf, -np.inf], np.nan
    )
    merged = merged.dropna(subset=["LATITUDE", "LONGITUDE"])
    if merged.empty:
        return None
    merged, hover_data, hover_labels = _formatted_hover_data(merged)
    fig = px.scatter_map(
        merged,
        lat="LATITUDE",
        lon="LONGITUDE",
        color=indicator_col,
        hover_name="NM_BAIRRO" if "NM_BAIRRO" in merged.columns else None,
        hover_data=hover_data,
        map_style="carto-darkmatter",
        center={"lat": -14.2, "lon": -51.9},
        zoom=3.1,
        opacity=0.78,
        template="plotly_dark",
        labels={**DISPLAY_NAMES, **hover_labels},
    )
    fig.update_traces(marker={"size": 7})
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        height=660,
        separators=",.",
    )
    return fig


def build_choropleth(indicators: pd.DataFrame, indicator_col: str):
    gdf = load_geodata()
    values = _prepare_values(indicators, indicator_col)
    if gdf is None or gdf.empty or values is None or values.empty:
        return None

    geo = gdf.copy()
    if "CD_BAIRRO" not in geo.columns:
        return None
    geo["CD_BAIRRO"] = geo["CD_BAIRRO"].astype("string")
    geo = geo.dropna(subset=["CD_BAIRRO"])
    if geo["CD_BAIRRO"].duplicated().any():
        raise ValueError("CD_BAIRRO deve ser unico na malha.")
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
    merged, hover_data, hover_labels = _formatted_hover_data(merged)
    fig = px.choropleth_map(
        merged,
        geojson=geojson,
        locations="CD_BAIRRO",
        featureidkey="properties.CD_BAIRRO",
        color=indicator_col,
        hover_name="NM_BAIRRO",
        hover_data=hover_data,
        map_style="carto-darkmatter",
        center={"lat": -12.8, "lon": -41.7},
        zoom=5.2,
        opacity=0.72,
        template="plotly_dark",
        labels={**DISPLAY_NAMES, **hover_labels},
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        height=660,
        separators=",.",
    )
    return fig
