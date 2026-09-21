import pandas as pd

from src.filters import filter_frame
from src.metrics import calcular_idr, proporcao_idosos, proporcao_jovens, representatividade_feminina


def test_calcular_idr_normalized_balanced_distribution():
    df = pd.DataFrame(
        {
            "CD_BAIRRO": ["1", "1", "1", "1"],
            "NM_BAIRRO": ["Centro"] * 4,
            "NM_MUN": ["Teste"] * 4,
            "Cor_Raca": ["Branca", "Preta", "Parda", "Indigena"],
            "valor": [25, 25, 25, 25],
        }
    )
    result = calcular_idr(df, "bairro")
    assert round(result.loc[0, "IDR"], 6) == 1


def test_representatividade_feminina_without_group():
    df = pd.DataFrame({"Sexo": ["Feminino", "Masculino"], "valor": [60, 40]})
    result = representatividade_feminina(df)
    assert result.loc[0, "Percentual"] == 60


def test_age_proportions():
    df = pd.DataFrame(
        {
            "Faixa_Etaria": ["0 a 14 anos", "15 a 29 anos", "60 anos ou mais"],
            "valor": [20, 50, 30],
        }
    )
    assert proporcao_jovens(df).loc[0, "Percentual"] == 20
    assert proporcao_idosos(df).loc[0, "Percentual"] == 30


def test_age_proportions_respond_to_age_filter_without_losing_suppressed_values():
    df = pd.DataFrame(
        {
            "Faixa_Etaria": ["0 a 14 anos", "15 a 29 anos", "60 anos ou mais"],
            "valor": pd.Series([20, 50, 30], dtype="Int64"),
        }
    )
    young_only = filter_frame(df, faixas=["0 a 14 anos"])
    adult_only = filter_frame(df, faixas=["15 a 29 anos"])
    assert proporcao_jovens(young_only).loc[0, "Percentual"] == 100
    assert proporcao_idosos(young_only).loc[0, "Percentual"] == 0
    assert proporcao_jovens(adult_only).loc[0, "Percentual"] == 0
    assert proporcao_idosos(adult_only).loc[0, "Percentual"] == 0

    suppressed_old = pd.DataFrame(
        {"Faixa_Etaria": ["60 anos ou mais"], "valor": pd.Series([pd.NA], dtype="Int64")}
    )
    assert pd.isna(proporcao_idosos(suppressed_old).loc[0, "Percentual"])


def test_grouped_proportion_uses_zero_only_when_category_is_absent():
    df = pd.DataFrame(
        {
            "CD_BAIRRO": ["1", "2"],
            "Faixa_Etaria": ["15 a 29 anos", "60 anos ou mais"],
            "valor": pd.Series([50, pd.NA], dtype="Int64"),
        }
    )
    result = proporcao_idosos(df, ["CD_BAIRRO"]).set_index("CD_BAIRRO")
    assert result.loc["1", "Percentual"] == 0
    assert pd.isna(result.loc["2", "Percentual"])
