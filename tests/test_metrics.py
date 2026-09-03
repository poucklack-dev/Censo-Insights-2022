import pandas as pd

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

