from __future__ import annotations

import pandas as pd


def sorted_options(series: pd.Series) -> list[str]:
    return sorted([value for value in series.dropna().astype(str).unique() if value])


def filter_frame(
    df: pd.DataFrame,
    ufs: list[str] | None = None,
    municipios: list[str] | None = None,
    bairros: list[str] | None = None,
    sexos: list[str] | None = None,
    faixas: list[str] | None = None,
    racas: list[str] | None = None,
) -> pd.DataFrame:
    result = df.copy()
    if ufs and "CD_UF" in result.columns:
        result = result[result["CD_UF"].astype("string").isin(ufs)]
    if municipios and "CD_MUN" in result.columns:
        result = result[result["CD_MUN"].astype("string").isin(municipios)]
    if bairros and "CD_BAIRRO" in result.columns:
        result = result[result["CD_BAIRRO"].astype("string").isin(bairros)]
    if sexos and "Sexo" in result.columns:
        result = result[result["Sexo"].isin(sexos)]
    if faixas:
        col = "Faixa_Etaria" if "Faixa_Etaria" in result.columns else "Faixa_Etaria_Original"
        if col in result.columns:
            accepted = set(faixas)
            if "30 a 59 anos" in accepted:
                accepted.update({"30 a 39 anos", "40 a 59 anos"})
            result = result[result[col].isin(accepted)]
    if racas and "Cor_Raca" in result.columns:
        result = result[result["Cor_Raca"].isin(racas)]
    return result
