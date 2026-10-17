from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from src import maps
from src.maps import _formatted_hover_data
from src.charts import bar_distribution, horizontal_ranking, population_diversity_by_band


def _scatter_frame(population, idr):
    return pd.DataFrame(
        {
            "NM_BAIRRO": [f"Bairro {index + 1}" for index in range(len(population))],
            "Populacao": population,
            "IDR": idr,
        }
    )


def test_population_diversity_chart_compares_mean_idr_by_population_band():
    fig = population_diversity_by_band(
        _scatter_frame([500, 2_000, 8_000, 30_000], [0.2, 0.4, 0.6, 0.8])
    )
    assert fig is not None
    assert fig.data[0].type == "bar"
    assert list(fig.data[0].x) == [
        "Até 1.000",
        "1.001–5.000",
        "5.001–20.000",
        "Acima de 20.000",
    ]
    assert list(fig.data[0].y) == [0.2, 0.4, 0.6, 0.8]
    assert fig.layout.yaxis.range == (0, 1)
    assert fig.data[0].hovertemplate is not None


@pytest.mark.parametrize(
    ("population", "idr", "expected_count"),
    [
        ([10, np.nan, 30], [0.2, 0.5, 0.8], 2),
        ([10, 20, 30], [0.2, np.nan, 0.8], 2),
        ([10, 0, 30], [0.2, 0.5, 0.8], 2),
        ([10, np.inf, 30], [0.2, 0.5, -np.inf], 1),
    ],
)
def test_population_diversity_chart_omits_invalid_values(population, idr, expected_count):
    source = _scatter_frame(population, idr)
    original = source.copy(deep=True)
    fig = population_diversity_by_band(source)
    if expected_count:
        assert fig is not None
        assert sum(
            int(label.split("<br>")[1].split()[0].replace(".", ""))
            for label in fig.data[0].text
        ) == expected_count
    else:
        assert fig is None
    pd.testing.assert_frame_equal(source, original)


def test_population_diversity_chart_accepts_nullable_numeric_dtypes():
    frame = _scatter_frame(
        pd.Series([10, pd.NA, 30], dtype="Int64"),
        pd.Series([0.2, 0.5, pd.NA], dtype="Float64"),
    )
    fig = population_diversity_by_band(frame)
    assert fig is not None
    assert list(fig.data[0].y) == [0.2]
    assert population_diversity_by_band(
        _scatter_frame([0, np.nan, 0], [0.1, 0.2, np.nan])
    ) is None


def test_chart_labels_use_brazilian_number_separators_and_short_precision():
    ranking = horizontal_ranking(
        pd.DataFrame({"NM_BAIRRO": ["Centro"], "Populacao": [1_234_567]}),
        "NM_BAIRRO",
        "Populacao",
        "Bairros mais populosos",
    )
    assert list(ranking.data[0].text) == ["1.234.567"]

    diversity = horizontal_ranking(
        pd.DataFrame({"NM_BAIRRO": ["Centro"], "IDR": [0.7851212]}),
        "NM_BAIRRO",
        "IDR",
        "Maior diversidade",
    )
    assert list(diversity.data[0].text) == ["0,79"]

    composition = bar_distribution(
        pd.DataFrame({"Cor_Raca": ["Branca", "Parda"], "valor": [50.595952, 49.404048]}),
        "Cor_Raca",
        percent=True,
        title="Composição",
    )
    labels = sorted(label for trace in composition.data for label in trace.text)
    assert labels == ["49,4%", "50,6%"]


def test_map_hover_values_are_rounded_and_grouped_for_display():
    frame = pd.DataFrame(
        {
            "Populacao": [1_234_567],
            "IDR": [0.7851212],
            "Representatividade feminina": [50.595952],
        }
    )
    displayed, hover_data, _ = _formatted_hover_data(frame)
    assert displayed.loc[0, "Populacao_exibicao"] == "1.234.567"
    assert displayed.loc[0, "IDR_exibicao"] == "0,79"
    assert displayed.loc[0, "Representatividade feminina_exibicao"] == "50,6%"
    assert hover_data["Populacao"] is False


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
