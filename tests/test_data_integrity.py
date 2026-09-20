from pathlib import Path

import pandas as pd
import pytest

from src.data_cleaning import clean_table
from src.filters import filter_frame


PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
EXPECTED_ROWS_PER_KEY = {
    "demo_age": 11,
    "demo_age_sex": 22,
    "race_population": 5,
    "race_sex": 10,
    "race_age": 20,
    "responsible_race": 5,
    "responsible_race_age": 25,
    "responsible_race_sex": 10,
}


def read_processed(name: str) -> pd.DataFrame:
    return pd.read_csv(
        PROCESSED / f"{name}.csv",
        sep=";",
        decimal=",",
        dtype={"CD_BAIRRO": "string", "CD_MUN": "string", "CD_UF": "string"},
    )


def test_dimension_and_fact_cardinalities_and_foreign_keys():
    bairro = read_processed("bairro")
    assert len(bairro) == 17_575
    assert bairro["CD_BAIRRO"].notna().all()
    assert bairro["CD_BAIRRO"].is_unique
    valid_keys = set(bairro["CD_BAIRRO"])
    for name, expected in EXPECTED_ROWS_PER_KEY.items():
        fact = read_processed(name)
        counts = fact.groupby("CD_BAIRRO", observed=True).size()
        assert counts.eq(expected).all(), name
        assert set(fact["CD_BAIRRO"]).issubset(valid_keys), name


def test_suppressed_and_missing_values_never_become_zero():
    raw = pd.DataFrame(
        {
            "CD_BAIRRO": ["1", "2", "3", "4"],
            "NM_BAIRRO": ["A", "B", "C", "D"],
            "V0001": ["0", "x", "", None],
        }
    )
    cleaned, log = clean_table(raw, "teste")
    assert cleaned.loc[0, "V0001"] == 0
    assert cleaned.loc[1:, "V0001"].isna().all()
    assert log["acao"].eq("preservacao_valor_suprimido").any()


def test_duplicate_counts_sum_but_rates_do_not_sum():
    raw = pd.DataFrame(
        {
            "CD_BAIRRO": ["1", "1"],
            "NM_BAIRRO": ["A", "A"],
            "v0001": ["10", "10"],
            "v0005": ["2", "4"],
            "v0006": ["0.1", "0.3"],
            "v0007": ["2", "6"],
            "AREA_KM2": ["1", "2"],
        }
    )
    cleaned, _ = clean_table(raw, "teste")
    row = cleaned.iloc[0]
    assert row["v0001"] == 20
    assert row["v0007"] == 8
    assert row["AREA_KM2"] == 3
    assert row["v0005"] == 3.5
    assert row["v0006"] == pytest.approx(0.25)


def test_combined_filters_use_territorial_codes_and_are_monotonic():
    df = pd.DataFrame(
        {
            "CD_UF": ["29", "29", "35"],
            "CD_MUN": ["1", "2", "3"],
            "CD_BAIRRO": ["10", "20", "30"],
            "NM_BAIRRO": ["Centro", "Centro", "Centro"],
            "Sexo": ["Feminino", "Masculino", "Feminino"],
            "Faixa_Etaria": ["0 a 14 anos", "15 a 29 anos", "0 a 14 anos"],
            "Cor_Raca": ["Parda", "Parda", "Branca"],
            "valor": [10, 20, 30],
        }
    )
    filtered = filter_frame(
        df,
        ufs=["29"],
        municipios=["1"],
        bairros=["10"],
        sexos=["Feminino"],
        faixas=["0 a 14 anos"],
        racas=["Parda"],
    )
    assert filtered["valor"].sum() == 10
    assert filtered["valor"].sum() <= df["valor"].sum()


def test_common_30_to_59_filter_maps_to_demography_subgroups():
    df = pd.DataFrame(
        {"Faixa_Etaria": ["30 a 39 anos", "40 a 59 anos", "60 anos ou mais"], "valor": [3, 4, 5]}
    )
    filtered = filter_frame(df, faixas=["30 a 59 anos"])
    assert filtered["valor"].sum() == 7


def test_fact_sum_does_not_grow_after_any_supported_filter():
    fact = read_processed("race_sex")
    total = fact["valor"].sum(min_count=1)
    sample = fact.iloc[0]
    filtered = filter_frame(
        fact,
        ufs=[str(sample.CD_UF)],
        municipios=[str(sample.CD_MUN)],
        bairros=[str(sample.CD_BAIRRO)],
        sexos=[str(sample.Sexo)],
        racas=[str(sample.Cor_Raca)],
    )
    assert filtered["valor"].sum(min_count=1) <= total
