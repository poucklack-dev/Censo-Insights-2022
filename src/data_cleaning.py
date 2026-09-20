from __future__ import annotations

import pandas as pd

from . import config
from .utils import normalize_key, remove_accents, to_numeric


def profile_table(df: pd.DataFrame, name: str) -> dict:
    return {
        "tabela": name,
        "registros": int(len(df)),
        "colunas": int(df.shape[1]),
        "duplicados_linha": int(df.duplicated().sum()),
        "duplicados_cd_bairro": int(df["CD_BAIRRO"].duplicated().sum())
        if "CD_BAIRRO" in df.columns
        else 0,
        "ausentes": df.isna().sum().sort_values(ascending=False).to_dict(),
        "tipos": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def clean_table(df: pd.DataFrame, name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = df.copy()
    log_rows = []
    for col in cleaned.columns:
        if col.upper().startswith("V") or col == "AREA_KM2":
            original = cleaned[col].astype("string").str.strip()
            suppressed = original.str.lower().eq("x")
            cleaned[col] = to_numeric(cleaned[col])
            if suppressed.any():
                log_rows.append(
                    {
                        "tabela": name,
                        "acao": "preservacao_valor_suprimido",
                        "quantidade": int(suppressed.sum()),
                        "motivo": f"Valores 'x' em {col} preservados como ausentes, nunca como zero.",
                    }
                )
        elif col.startswith("CD_"):
            cleaned[col] = cleaned[col].astype("string").map(normalize_key)
        else:
            cleaned[col] = cleaned[col].astype("string").map(normalize_key)
    if "NM_BAIRRO" in cleaned.columns:
        cleaned["NM_BAIRRO_NORMALIZADO"] = cleaned["NM_BAIRRO"].map(lambda x: remove_accents(x).title())
    if "NM_MUN" in cleaned.columns:
        cleaned["NM_MUN_NORMALIZADO"] = cleaned["NM_MUN"].map(lambda x: remove_accents(x).title())

    duplicate_count = int(cleaned["CD_BAIRRO"].duplicated().sum()) if "CD_BAIRRO" in cleaned else 0
    if duplicate_count:
        numeric_cols = cleaned.select_dtypes(include="number").columns.tolist()
        text_cols = [col for col in cleaned.columns if col not in numeric_cols and col != "CD_BAIRRO"]
        unique_part = cleaned[~cleaned["CD_BAIRRO"].duplicated(keep=False)]
        duplicate_part = cleaned[cleaned["CD_BAIRRO"].duplicated(keep=False)]
        rows = []
        for cd_bairro, group in duplicate_part.groupby("CD_BAIRRO", dropna=False):
            row = {"CD_BAIRRO": cd_bairro}
            for col in numeric_cols:
                if col in {"v0005", "v0006"} and "v0007" in group:
                    valid = group[col].notna() & group["v0007"].notna()
                    weights = group.loc[valid, "v0007"]
                    row[col] = (
                        (group.loc[valid, col] * weights).sum(min_count=1) / weights.sum(min_count=1)
                        if valid.any() and weights.sum(min_count=1) > 0
                        else group[col].mean()
                    )
                else:
                    # The duplicate rows are territorial pieces of the same code.
                    # Counts and area are additive even when the two values coincide.
                    row[col] = group[col].sum(min_count=1)
            for col in text_cols:
                row[col] = group[col].dropna().iloc[0] if group[col].notna().any() else pd.NA
            rows.append(row)
        cleaned = pd.concat([unique_part, pd.DataFrame(rows)], ignore_index=True)
        log_rows.append(
            {
                "tabela": name,
                "acao": "agrupamento_por_cd_bairro",
                "quantidade": duplicate_count,
                "motivo": "Chave CD_BAIRRO repetida; valores numericos iguais foram preservados uma vez e valores distintos seriam somados.",
            }
        )
        log_rows[-1]["motivo"] = (
            "Chave repetida consolidada: contagens/area somadas; medias e percentuais "
            "v0005/v0006 ponderados por domicilios ocupados; conflitos textuais registrados pela primeira ocorrencia."
        )
    for col in cleaned.columns:
        if col.upper().startswith("V") and col.lower() not in {"v0005", "v0006"}:
            numeric = pd.to_numeric(cleaned[col], errors="coerce")
            if numeric.dropna().mod(1).eq(0).all():
                cleaned[col] = numeric.astype("Int64")
    return cleaned, pd.DataFrame(log_rows)


def clean_raw_tables(raw_tables: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    profiles = [profile_table(df, name) for name, df in raw_tables.items()]
    cleaned = {}
    logs = []
    for name, df in raw_tables.items():
        cleaned_df, log_df = clean_table(df, name)
        cleaned[name] = cleaned_df
        if not log_df.empty:
            logs.append(log_df)
    treatment_log = pd.concat(logs, ignore_index=True) if logs else pd.DataFrame(
        columns=["tabela", "acao", "quantidade", "motivo"]
    )
    profile_df = pd.DataFrame(
        [
            {
                "tabela": item["tabela"],
                "registros": item["registros"],
                "colunas": item["colunas"],
                "duplicados_linha": item["duplicados_linha"],
                "duplicados_cd_bairro": item["duplicados_cd_bairro"],
            }
            for item in profiles
        ]
    )
    return cleaned, treatment_log, profile_df


def detect_inconsistencies(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bairro = model["bairro"]
    checks = []
    if {"populacao_total", "pop_demografia_total"}.issubset(bairro.columns):
        diff = (bairro["populacao_total"] - bairro["pop_demografia_total"]).abs()
        checks.append(
            {
                "validacao": "Populacao basica x demografia",
                "registros_afetados": int((diff > 0).sum()),
                "maior_diferenca": float(diff.max()),
                "status": "OK" if (diff == 0).all() else "Atencao",
            }
        )
    if "race_population" in model:
        race_total = model["race_population"].groupby("CD_BAIRRO")["valor"].sum(min_count=1)
        expected = bairro.set_index("CD_BAIRRO")["populacao_total"]
        diff = (race_total.reindex(expected.index) - expected).abs()
        checks.append(
            {
                "validacao": "Soma cor/raca x populacao",
                "registros_afetados": int((diff > 0).sum()),
                "maior_diferenca": float(diff.max()),
                "status": "OK" if (diff == 0).all() else "Atencao",
            }
        )
    return pd.DataFrame(checks)
