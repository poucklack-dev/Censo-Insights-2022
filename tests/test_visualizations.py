from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from src import maps
from src.charts import scatter_diversity_population


def _scatter_frame(population, idr):
    return pd.DataFrame(
        {"NM_BAIRRO": ["A", "B", "C"], "Populacao": population, "IDR": idr}
    )


def test_scatter_diversity_with_complete_data():
    fig = scatter_diversity_population(_scatter_frame([10, 20, 30], [0.2, 0.5, 0.8]), "NM_BAIRRO")
    assert fig is not None
    assert list(fig.data[0].marker.size) == [10.0, 20.0, 30.0]


@pytest.mark.parametrize(
    ("population", "idr", "expected"),
    [
        ([10, np.nan, 30], [0.2, 0.5, 0.8], 2),
        ([10, 20, 30], [0.2, np.nan, 0.8], 2),
        ([10, 0, 30], [0.2, 0.5, 0.8], 2),
        ([10, np.inf, 30], [0.2, 0.5, -np.inf], 1),
    ],
)
def test_scatter_omits_values_invalid_only_for_plot(population, idr, expected):
    source = _scatter_frame(population, idr)
    original = source.copy(deep=True)
    fig = scatter_diversity_population(source, "NM_BAIRRO")
    assert fig is not None
    assert len(fig.data[0].x) == expected
    pd.testing.assert_frame_equal(source, original)


def test_scatter_accepts_nullable_numeric_dtypes_and_empty_result():
    frame = _scatter_frame(
        pd.Series([10, pd.NA, 30], dtype="Int64"),
        pd.Series([0.2, 0.5, pd.NA], dtype="Float64"),
    )
    fig = scatter_diversity_population(frame, "NM_BAIRRO")
    assert fig is not None
    assert fig.data[0].x.dtype == np.dtype("float64")
    assert fig.data[0].y.dtype == np.dtype("float64")
    assert scatter_diversity_population(_scatter_frame([0, np.nan, 0], [0.1, 0.2, np.nan]), "NM_BAIRRO") is None


def _geodata():
    return gpd.GeoDataFrame(
        {
            "CD_BAIRRO": ["1", "2"],
            "NM_BAIRRO": ["Centro", "Norte"],
            "NM_MUN": ["Cidade", "Cidade"],
        },
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        ],
        crs="EPSG:4326",
    )


@pytest.mark.parametrize(
    "indicator",
    ["Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"],
)
def test_map_supports_all_indicators_with_explicit_neighborhood_key(monkeypatch, indicator):
    monkeypatch.setattr(maps, "load_geodata", _geodata)
    indicators = pd.DataFrame(
        {
            "CD_BAIRRO": pd.Series([1, 2], dtype="Int64"),
            "NM_BAIRRO": ["Centro", "Norte"],
            "NM_MUN": ["Cidade", "Cidade"],
            indicator: [10.0, 20.0],
        }
    )
    fig = maps.build_choropleth(indicators, indicator)
    assert fig is not None
    assert list(fig.data[0].locations) == ["1", "2"]
    assert fig.data[0].featureidkey == "properties.CD_BAIRRO"
    assert "mapbox" not in fig.data[0].type


def test_map_returns_none_without_geographic_match(monkeypatch):
    monkeypatch.setattr(maps, "load_geodata", _geodata)
    indicators = pd.DataFrame({"CD_BAIRRO": ["999"], "IDR": [0.5]})
    assert maps.build_choropleth(indicators, "IDR") is None


def test_map_requires_one_to_one_keys(monkeypatch):
    monkeypatch.setattr(maps, "load_geodata", _geodata)
    indicators = pd.DataFrame({"CD_BAIRRO": ["1", "1"], "IDR": [0.5, 0.6]})
    with pytest.raises(ValueError, match="CD_BAIRRO deve ser unico"):
        maps.build_choropleth(indicators, "IDR")


@pytest.mark.parametrize(
    "indicator",
    ["Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"],
)
def test_national_point_map_supports_all_indicators(monkeypatch, indicator):
    points = pd.DataFrame(
        {
            "CD_BAIRRO": ["1", "2"],
            "LATITUDE": [-12.0, -23.0],
            "LONGITUDE": [-38.0, -46.0],
        }
    )
    monkeypatch.setattr(maps, "load_neighborhood_points", lambda: points)
    indicators = pd.DataFrame(
        {
            "CD_BAIRRO": pd.Series([1, 2], dtype="Int64"),
            "NM_BAIRRO": ["Centro", "Norte"],
            "NM_MUN": ["Cidade A", "Cidade B"],
            "NM_UF": ["Bahia", "São Paulo"],
            indicator: [10.0, 20.0],
        }
    )
    fig = maps.build_point_map(indicators, indicator)
    assert fig is not None
    assert fig.data[0].type == "scattermap"
    assert list(fig.data[0].lat) == [-12.0, -23.0]
    assert list(fig.data[0].lon) == [-38.0, -46.0]


def test_national_point_map_returns_none_without_match(monkeypatch):
    points = pd.DataFrame(
        {"CD_BAIRRO": ["1"], "LATITUDE": [-12.0], "LONGITUDE": [-38.0]}
    )
    monkeypatch.setattr(maps, "load_neighborhood_points", lambda: points)
    indicators = pd.DataFrame({"CD_BAIRRO": ["999"], "IDR": [0.5]})
    assert maps.build_point_map(indicators, "IDR") is None


def test_repository_has_no_legacy_mapbox_api():
    source = (Path(__file__).parents[1] / "src" / "maps.py").read_text(encoding="utf-8")
    legacy_names = (
        "choropleth_mapbox",
        "scatter_mapbox",
        "line_mapbox",
        "density_mapbox",
        "mapbox_access_token",
        "MAPBOX_TOKEN",
    )
    assert not any(name in source for name in legacy_names)
