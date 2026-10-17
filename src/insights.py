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
from .interactivity import (
    age_source,
    female_responsibility_source,
    population_source,
    racial_source,
    responsible_race_source,
)


def _top_by_population(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty or "valor" not in frame or not all(column in frame for column in group_cols):
        return pd.DataFrame()
    return (
        frame.groupby(group_cols, dropna=False, observed=True)["valor"]
        .sum(min_count=1)
        .rename("valor")
        .reset_index()
        .sort_values("valor", ascending=False)
        .head(1)
    )


def gerar_insights_demograficos(
    model: dict[str, pd.DataFrame], filtros: dict | None = None
) -> list[str]:
    filtros = filtros or {}
    population = population_source(model, filtros)
    top_pop = _top_by_population(population, ["NM_MUN", "NM_BAIRRO"]) if population is not None else pd.DataFrame()
    insights = []
    if not top_pop.empty:
        row = top_pop.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, reúne a maior população no recorte atual: {br_number(row['valor'])} pessoas."
        )
    if not filtros.get("faixas"):
        ages = age_source(model, filtros)
        if ages is not None:
            jovens = proporcao_jovens(ages, ["NM_MUN", "NM_BAIRRO"]).sort_values("Percentual", ascending=False).head(1)
            if not jovens.empty and pd.notna(jovens.iloc[0]["Percentual"]):
                row = jovens.iloc[0]
                insights.append(
                    f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, tem a maior participação de crianças de 0 a 14 anos: {br_percent(row['Percentual'])}."
                )
    return insights


def gerar_insights_raciais(
    model: dict[str, pd.DataFrame], filtros: dict | None = None
) -> list[str]:
    racial = racial_source(model, filtros or {})
    if racial is None or racial.empty:
        return []
    idr_mun = calcular_idr(racial, "municipio").head(1)
    idr_bairro = calcular_idr(racial, "bairro").head(1)
    insights = []
    selected_groups = racial["Cor_Raca"].nunique() if "Cor_Raca" in racial else 0
    if selected_groups > 1 and not idr_mun.empty and pd.notna(idr_mun.iloc[0]["IDR"]):
        row = idr_mun.iloc[0]
        insights.append(f"{row['NM_MUN']} tem o maior IDR municipal no recorte atual: {row['IDR']:.3f}.")
    if selected_groups > 1 and not idr_bairro.empty and pd.notna(idr_bairro.iloc[0]["IDR"]):
        row = idr_bairro.iloc[0]
        insights.append(f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, tem o maior IDR entre bairros: {row['IDR']:.3f}.")
    return insights


def gerar_insights_responsaveis(
    model: dict[str, pd.DataFrame], filtros: dict | None = None
) -> list[str]:
    filtros = filtros or {}
    responsibility = female_responsibility_source(model, filtros)
    rep = (
        representatividade_feminina(responsibility, ["NM_MUN", "NM_BAIRRO"]).sort_values("Percentual", ascending=False)
        if responsibility is not None
        else pd.DataFrame()
    )
    responsible_race = responsible_race_source(model, filtros)
    indig = (
        ranking_responsaveis_indigenas_40mais(model["responsible_race_age"]).head(1)
        if responsible_race is not None and not filtros.get("sexos")
        else pd.DataFrame()
    )
    insights = []
    if not rep.empty and pd.notna(rep.iloc[0]["Percentual"]):
        row = rep.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, apresenta a maior participação feminina entre responsáveis: {br_percent(row['Percentual'])}."
        )
    if not indig.empty:
        row = indig.iloc[0]
        insights.append(
            f"{row['NM_BAIRRO']}, em {row['NM_MUN']}, tem mais responsáveis indígenas com 40 anos ou mais: {br_number(row['Quantidade'])} pessoas."
        )
    return insights


def gerar_insights_etarios(
    model: dict[str, pd.DataFrame], filtros: dict | None = None
) -> list[str]:
    filtros = filtros or {}
    ages = age_source(model, filtros)
    if ages is None:
        return []
    if filtros.get("faixas"):
        top_age = _top_by_population(ages, ["NM_MUN", "NM_BAIRRO"])
        if top_age.empty:
            return []
        row = top_age.iloc[0]
        faixa = ", ".join(map(str, filtros["faixas"]))
        return [
            f"Nas faixas etárias selecionadas ({faixa}), {row['NM_BAIRRO']}, em {row['NM_MUN']}, reúne o maior contingente: {br_number(row['valor'])} pessoas."
        ]
    idosos = proporcao_idosos(ages, ["NM_MUN", "NM_BAIRRO"]).sort_values("Percentual", ascending=False).head(3)
    if idosos.empty:
        return []
    nomes = ", ".join(f"{row.NM_BAIRRO} ({row.NM_MUN})" for row in idosos.itertuples())
    return [f"A população com 60 anos ou mais tem maior participação relativa nos bairros {nomes}."]


def all_insights(model: dict[str, pd.DataFrame], filtros: dict | None = None) -> list[str]:
    filtros = filtros or {}
    insights = []
    for generator in [
        gerar_insights_demograficos,
        gerar_insights_raciais,
        gerar_insights_responsaveis,
        gerar_insights_etarios,
    ]:
        insights.extend(generator(model, filtros))
    return insights

