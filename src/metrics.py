from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def calcular_idr(df: pd.DataFrame, nivel: str = "bairro") -> pd.DataFrame:
    """Normalized Simpson diversity index: (1 - sum(p_i^2)) / (1 - 1/k), from 0 to 1."""
    level_map = {"bairro": ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"], "municipio": ["CD_MUN", "NM_MUN"]}
    group_cols = [col for col in level_map.get(nivel, [nivel]) if col in df.columns]
    if not group_cols:
        raise ValueError("Nivel invalido ou ausente nos dados.")
    if df.empty:
        return pd.DataFrame(columns=group_cols + ["IDR", "categorias", "Populacao"])
    grouped = df.groupby(group_cols + ["Cor_Raca"], dropna=False)["valor"].sum().reset_index()
    totals = grouped.groupby(group_cols)["valor"].transform("sum")
    grouped["proporcao"] = np.where(totals > 0, grouped["valor"] / totals, 0)
    k = grouped[grouped["valor"] > 0].groupby(group_cols)["Cor_Raca"].nunique().rename("categorias")
    simpson = grouped.groupby(group_cols)["proporcao"].apply(lambda s: 1 - np.square(s).sum())
    result = pd.concat([simpson.rename("IDR"), k], axis=1).reset_index()
    result["IDR"] = np.where(
        result["categorias"] > 1,
        result["IDR"] / (1 - 1 / result["categorias"]),
        0,
    )
    population = df.groupby(group_cols)["valor"].sum().rename("Populacao").reset_index()
    result = result.merge(population, on=group_cols, how="left")
    return result.sort_values("IDR", ascending=False)


def population_total(df: pd.DataFrame) -> float:
    if "populacao_total" in df.columns:
        return float(df["populacao_total"].sum())
    return float(df["valor"].sum()) if "valor" in df.columns else 0.0


def percent_by_group(df: pd.DataFrame, group_cols: list[str], mask: pd.Series) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_cols + ["Total", "Quantidade", "Percentual"])
    if not group_cols:
        total = df["valor"].sum()
        quantity = df.loc[mask, "valor"].sum()
        return pd.DataFrame(
            [{"Total": total, "Quantidade": quantity, "Percentual": safe_divide(quantity, total) * 100}]
        )
    base = df.groupby(group_cols, dropna=False)["valor"].sum().rename("Total")
    subset = df[mask].groupby(group_cols, dropna=False)["valor"].sum().rename("Quantidade")
    result = pd.concat([base, subset], axis=1).fillna(0).reset_index()
    result["Percentual"] = np.where(result["Total"] > 0, result["Quantidade"] / result["Total"] * 100, 0)
    return result


def representatividade_feminina(responsible_race_sex: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    return percent_by_group(
        responsible_race_sex,
        group_cols,
        responsible_race_sex["Sexo"].eq("Feminino"),
    )


def proporcao_jovens(demo_age: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    return percent_by_group(demo_age, group_cols, demo_age["Faixa_Etaria"].eq("0 a 14 anos"))


def proporcao_idosos(demo_age: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    return percent_by_group(demo_age, group_cols, demo_age["Faixa_Etaria"].eq("60 anos ou mais"))


def idade_media_estimada(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    temp = df.copy()
    temp["peso_idade"] = temp["valor"] * temp["Faixa_Etaria"].map(config.AGE_MIDPOINT)
    grouped = temp.groupby(group_cols, dropna=False).agg(valor=("valor", "sum"), peso_idade=("peso_idade", "sum"))
    grouped["Idade_Media_Estimada"] = np.where(grouped["valor"] > 0, grouped["peso_idade"] / grouped["valor"], np.nan)
    return grouped.reset_index()


def ranking_jovens_pardos(race_age: pd.DataFrame) -> pd.DataFrame:
    result = percent_by_group(
        race_age,
        ["CD_MUN", "NM_MUN", "CD_BAIRRO", "NM_BAIRRO"],
        race_age["Faixa_Etaria"].eq("0 a 14 anos") & race_age["Cor_Raca"].eq("Parda"),
    )
    result = result.rename(columns={"Quantidade": "Jovens_Pardos", "Total": "Populacao"})
    return result.sort_values(["Percentual", "Jovens_Pardos"], ascending=False)


def predominant_race(race_population: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = race_population.groupby(group_cols + ["Cor_Raca"], dropna=False)["valor"].sum().reset_index()
    idx = grouped.sort_values("valor", ascending=False).groupby(group_cols).head(1).index
    return grouped.loc[idx, group_cols + ["Cor_Raca"]].rename(columns={"Cor_Raca": "Grupo racial predominante"})


def ranking_municipios_diversidade(race_population: pd.DataFrame) -> pd.DataFrame:
    idr = calcular_idr(race_population, nivel="municipio")
    pred = predominant_race(race_population, ["CD_MUN", "NM_MUN"])
    result = idr.merge(pred, on=["CD_MUN", "NM_MUN"], how="left")
    result = result.rename(columns={"NM_MUN": "Municipio"})
    result.insert(0, "Posicao", range(1, len(result) + 1))
    return result


def ranking_responsaveis_indigenas_40mais(responsible_race_age: pd.DataFrame) -> pd.DataFrame:
    mask = responsible_race_age["Cor_Raca"].eq("Indigena") & responsible_race_age["Eh_40_Mais"]
    result = percent_by_group(
        responsible_race_age,
        ["CD_MUN", "NM_MUN", "CD_BAIRRO", "NM_BAIRRO"],
        mask,
    )
    result = result.rename(columns={"Quantidade": "Quantidade", "Total": "Total_Responsaveis"})
    return result.sort_values(["Percentual", "Quantidade"], ascending=False)

def kpis(model: dict[str, pd.DataFrame]) -> dict[str, float]:
    bairro = model["bairro"]
    race_population = model["race_population"]
    rep = representatividade_feminina(model["responsible_race_sex"])["Percentual"].iloc[0]
    jovens = proporcao_jovens(model["demo_age"])["Percentual"].iloc[0]
    idosos = proporcao_idosos(model["demo_age"])["Percentual"].iloc[0]
    idr = calcular_idr(race_population, "bairro")
    return {
        "Populacao total": population_total(bairro),
        "Municipios": bairro["CD_MUN"].nunique(),
        "Bairros": bairro["CD_BAIRRO"].nunique(),
        "IDR medio": idr["IDR"].mean(),
        "Representatividade feminina": rep,
        "Jovens": jovens,
        "Idosos": idosos,
    }
