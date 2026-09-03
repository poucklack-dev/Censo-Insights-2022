from __future__ import annotations

import pandas as pd

from .metrics import (
    calcular_idr,
    proporcao_idosos,
    proporcao_jovens,
    ranking_responsaveis_indigenas_40mais,
    representatividade_feminina,
)
from .utils import br_number, br_percent


def gerar_insights_demograficos(model: dict[str, pd.DataFrame]) -> list[str]:
    bairro = model["bairro"]
    top_pop = bairro.sort_values("populacao_total", ascending=False).head(1)
    insights = []
    if not top_pop.empty:
        row = top_pop.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, e o bairro mais populoso do recorte, com {br_number(row['populacao_total'])} pessoas."
        )
    jovens = proporcao_jovens(model["demo_age"], ["NM_MUN", "NM_BAIRRO"]).sort_values("Percentual", ascending=False).head(1)
    if not jovens.empty:
        row = jovens.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, concentra a maior proporcao de jovens: {br_percent(row['Percentual'])} da populacao."
        )
    return insights


def gerar_insights_raciais(model: dict[str, pd.DataFrame]) -> list[str]:
    idr_mun = calcular_idr(model["race_population"], "municipio").head(1)
    idr_bairro = calcular_idr(model["race_population"], "bairro").head(1)
    insights = []
    if not idr_mun.empty:
        row = idr_mun.iloc[0]
        insights.append(f"{row['NM_MUN']} lidera a diversidade racial municipal, com IDR {row['IDR']:.3f}.")
    if not idr_bairro.empty:
        row = idr_bairro.iloc[0]
        insights.append(f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, tem o maior IDR entre bairros: {row['IDR']:.3f}.")
    return insights


def gerar_insights_responsaveis(model: dict[str, pd.DataFrame]) -> list[str]:
    rep = representatividade_feminina(model["responsible_race_sex"], ["NM_MUN", "NM_BAIRRO"]).sort_values(
        "Percentual", ascending=False
    )
    indig = ranking_responsaveis_indigenas_40mais(model["responsible_race_age"]).head(1)
    insights = []
    if not rep.empty:
        row = rep.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, apresenta a maior representatividade feminina entre responsaveis: {br_percent(row['Percentual'])}."
        )
    if not indig.empty:
        row = indig.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, se destaca em responsaveis indigenas com 40 anos ou mais: {br_number(row['Quantidade'])} registros."
        )
    return insights


def gerar_insights_etarios(model: dict[str, pd.DataFrame]) -> list[str]:
    idosos = proporcao_idosos(model["demo_age"], ["NM_MUN", "NM_BAIRRO"]).sort_values("Percentual", ascending=False).head(3)
    if idosos.empty:
        return []
    nomes = ", ".join(f"{row.NM_BAIRRO} ({row.NM_MUN})" for row in idosos.itertuples())
    return [f"A populacao idosa tem maior concentracao relativa nos bairros {nomes}."]


def all_insights(model: dict[str, pd.DataFrame]) -> list[str]:
    insights = []
    for generator in [
        gerar_insights_demograficos,
        gerar_insights_raciais,
        gerar_insights_responsaveis,
        gerar_insights_etarios,
    ]:
        insights.extend(generator(model))
    return insights

