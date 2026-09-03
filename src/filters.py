from __future__ import annotations

import pandas as pd


def sorted_options(series: pd.Series) -> list[str]:
    return sorted([value for value in series.dropna().astype(str).unique() if value])


def filter_frame(
    df: pd.DataFrame,
    municipios: list[str] | None = None,
    bairros: list[str] | None = None,
    sexos: list[str] | None = None,
    faixas: list[str] | None = None,
    racas: list[str] | None = None,
) -> pd.DataFrame:
    result = df.copy()
    if municipios and "NM_MUN" in result.columns:
        result = result[result["NM_MUN"].isin(municipios)]
    if bairros and "NM_BAIRRO" in result.columns:
        result = result[result["NM_BAIRRO"].isin(bairros)]
    if sexos and "Sexo" in result.columns:
        result = result[result["Sexo"].isin(sexos)]
    if faixas:
        col = "Faixa_Etaria" if "Faixa_Etaria" in result.columns else "Faixa_Etaria_Original"
        if col in result.columns:
            result = result[result[col].isin(faixas)]
    if racas and "Cor_Raca" in result.columns:
        result = result[result["Cor_Raca"].isin(racas)]
    return result

