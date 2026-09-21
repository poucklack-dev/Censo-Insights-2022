from __future__ import annotations

import pandas as pd


def _selected(filters: dict, key: str) -> bool:
    return bool(filters.get(key))


def racial_source(
    model: dict[str, pd.DataFrame], filters: dict
) -> pd.DataFrame | None:
    """Fact table that preserves the selected dimensions plus race."""
    has_sex = _selected(filters, "sexos")
    has_age = _selected(filters, "faixas")
    if has_sex and has_age:
        return None
    if has_sex:
        return model["race_sex"]
    if has_age:
        return model["race_age"]
    return model["race_population"]


def age_source(
    model: dict[str, pd.DataFrame], filters: dict
) -> pd.DataFrame | None:
    """Fact table that preserves the selected dimensions plus age."""
    has_sex = _selected(filters, "sexos")
    has_race = _selected(filters, "racas")
    if has_sex and has_race:
        return None
    if has_sex:
        return model["demo_age_sex"]
    if has_race:
        return model["race_age"]
    return model["demo_age"]


def female_responsibility_source(
    model: dict[str, pd.DataFrame], filters: dict
) -> pd.DataFrame | None:
    """Female responsibility has no published joint age-by-sex fact."""
    if _selected(filters, "faixas"):
        return None
    return model["responsible_race_sex"]


def population_source(
    model: dict[str, pd.DataFrame], filters: dict
) -> pd.DataFrame | None:
    """Return a fact with a standardized ``valor`` column for the selected dimensions."""
    has_sex = _selected(filters, "sexos")
    has_age = _selected(filters, "faixas")
    has_race = _selected(filters, "racas")
    if has_sex and has_age and has_race:
        return None
    if has_sex and has_race:
        return model["race_sex"]
    if has_sex and has_age:
        return model["demo_age_sex"]
    if has_race and has_age:
        return model["race_age"]
    if has_race:
        return model["race_population"]
    if has_age:
        return model["demo_age"]
    if has_sex:
        return model["demo_age_sex"]
    return model["bairro"].rename(columns={"populacao_total": "valor"})


def responsible_race_source(
    model: dict[str, pd.DataFrame], filters: dict
) -> pd.DataFrame | None:
    """Responsible-person race source respecting either sex or age."""
    has_sex = _selected(filters, "sexos")
    has_age = _selected(filters, "faixas")
    if has_age:
        return None
    if has_sex:
        return model["responsible_race_sex"]
    return model["responsible_race"]


def unavailable_reason(filters: dict) -> str:
    dimensions = []
    if _selected(filters, "sexos"):
        dimensions.append("sexo")
    if _selected(filters, "faixas"):
        dimensions.append("idade")
    if _selected(filters, "racas"):
        dimensions.append("cor ou raça")
    selection = ", ".join(dimensions)
    return (
        f"Indicador indisponível para a combinação selecionada ({selection}). "
        "O Censo 2022 não publicou esse cruzamento de dimensões na base utilizada."
    )
