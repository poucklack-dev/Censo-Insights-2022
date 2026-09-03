from __future__ import annotations

import re
import unicodedata
from io import BytesIO

import pandas as pd


def normalize_key(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def remove_accents(value: object) -> str:
    text = normalize_key(value)
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )


def br_number(value: float | int | None, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def br_percent(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{br_number(value, decimals)}%"


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace({".": pd.NA, "-": pd.NA, "": pd.NA}), errors="coerce")


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def dataframe_to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, sheet_df in sheets.items():
            safe_name = name[:31]
            sheet_df.to_excel(writer, sheet_name=safe_name, index=False)
    return output.getvalue()

