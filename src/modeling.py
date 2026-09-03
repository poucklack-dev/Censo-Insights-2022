from __future__ import annotations

import pandas as pd

from . import config

FACT_GEO_COLUMNS = ["CD_MUN", "NM_MUN", "CD_BAIRRO", "NM_BAIRRO"]


def _optimize_fact(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    if "valor" in result.columns:
        result["valor"] = pd.to_numeric(result["valor"], errors="coerce").fillna(0).astype("int32")
    for col in result.select_dtypes(include=["object", "string"]).columns:
        result[col] = result[col].astype("category")
    return result


def _melt_mapping(
    source: pd.DataFrame,
    mapping: dict,
    value_name: str = "valor",
    extra_names: tuple[str, ...] = (),
) -> pd.DataFrame:
    rows = []
    base_cols = [col for col in FACT_GEO_COLUMNS if col in source.columns]
    for key, col in mapping.items():
        if col not in source.columns:
            continue
        piece = source[base_cols + [col]].copy()
        keys = key if isinstance(key, tuple) else (key,)
        for name, value in zip(extra_names or ("categoria",), keys):
            piece[name] = value
        piece = piece.rename(columns={col: value_name})
        rows.append(piece)
    if not rows:
        return pd.DataFrame()
    return _optimize_fact(pd.concat(rows, ignore_index=True))


def build_model(cleaned: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    basic = cleaned["basico"]
    geo_attrs = basic[[col for col in config.GEO_COLUMNS if col in basic.columns]].drop_duplicates("CD_BAIRRO")
    race = cleaned["cor_raca"].drop(columns=["NM_BAIRRO"], errors="ignore").merge(
        geo_attrs, on="CD_BAIRRO", how="left"
    )
    demo = cleaned["demografia"].drop(columns=["NM_BAIRRO"], errors="ignore").merge(
        geo_attrs, on="CD_BAIRRO", how="left"
    )

    bairro = basic.copy()
    bairro = bairro.rename(
        columns={
            "v0001": "populacao_total",
            "v0002": "domicilios_total",
            "v0005": "media_moradores_dpo",
            "v0006": "pct_dpo_imputados",
            "v0007": "domicilios_ocupados",
        }
    )
    for old, new in {
        "V01006": "pop_demografia_total",
        "V01007": "pop_masculina",
        "V01008": "pop_feminina",
    }.items():
        if old in demo.columns:
            bairro = bairro.merge(demo[["CD_BAIRRO", old]], on="CD_BAIRRO", how="left")
            bairro = bairro.rename(columns={old: new})
    for col in bairro.select_dtypes(include=["object", "string"]).columns:
        bairro[col] = bairro[col].astype("category")

    race_population = _melt_mapping(race, config.RACE_TOTAL_COLS, extra_names=("Cor_Raca",))
    race_sex = _melt_mapping(race, config.RACE_SEX_COLS, extra_names=("Sexo", "Cor_Raca"))
    race_age = _melt_mapping(race, config.RACE_AGE_COLS, extra_names=("Faixa_Etaria", "Cor_Raca"))

    responsible_race = _melt_mapping(race, config.RESP_RACE_TOTAL_COLS, extra_names=("Cor_Raca",))
    responsible_race_sex = _melt_mapping(
        race, config.RESP_RACE_SEX_COLS, extra_names=("Cor_Raca", "Sexo")
    )
    responsible_race_age = _melt_mapping(
        race, config.RESP_RACE_AGE_COLS, extra_names=("Cor_Raca", "Faixa_Etaria")
    )
    if not responsible_race_age.empty:
        responsible_race_age["Eh_40_Mais"] = responsible_race_age["Faixa_Etaria"].isin(
            ["40 a 59 anos", "60 anos ou mais"]
        )

    demo_age = _melt_mapping(demo, config.DEMO_AGE_COLS, extra_names=("Faixa_Etaria_Original",))
    if not demo_age.empty:
        demo_age["Faixa_Etaria"] = demo_age["Faixa_Etaria_Original"].map(config.AGE_TO_REQUIRED_GROUP)
        demo_age["Eh_Jovem"] = demo_age["Faixa_Etaria"].eq("0 a 14 anos")
        demo_age["Eh_Idoso"] = demo_age["Faixa_Etaria"].eq("60 anos ou mais")
        demo_age["Ponto_Medio_Estimado"] = demo_age["Faixa_Etaria_Original"].map(config.AGE_MIDPOINT)

    demo_age_sex = _melt_mapping(
        demo, config.DEMO_AGE_SEX_COLS, extra_names=("Sexo", "Faixa_Etaria_Original")
    )
    if not demo_age_sex.empty:
        demo_age_sex["Faixa_Etaria"] = demo_age_sex["Faixa_Etaria_Original"].map(
            config.AGE_TO_REQUIRED_GROUP
        )
        demo_age_sex["Ponto_Medio_Estimado"] = demo_age_sex["Faixa_Etaria_Original"].map(
            config.AGE_MIDPOINT
        )

    return {
        "bairro": bairro,
        "race_population": race_population,
        "race_sex": race_sex,
        "race_age": race_age,
        "responsible_race": responsible_race,
        "responsible_race_sex": responsible_race_sex,
        "responsible_race_age": responsible_race_age,
        "demo_age": demo_age,
        "demo_age_sex": demo_age_sex,
    }
