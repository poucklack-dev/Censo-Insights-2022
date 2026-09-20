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


def classify_neighborhood_name(value: object) -> str:
    """Diagnostic classification only; it never determines record validity."""
    text = normalize_key(value)
    if not text:
        return "NULO"
    if text.isnumeric():
        return "NUMERICO"
    if len(text) <= 4:
        return "CURTO"
    if any(char.isalpha() for char in text) and any(char.isdigit() for char in text):
        return "ALFANUMERICO"
    compact = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", text).lower()
    repeated_block = re.fullmatch(r"(.{1,3})\1+", compact)
    if len(compact) >= 4 and (len(set(compact)) <= 2 or repeated_block):
        return "REPETITIVO"
    return "NORMAL"


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
    """Parse published numbers without turning missing/suppressed values into zero."""
    normalized = series.astype("string").str.strip().replace(
        {".": pd.NA, "-": pd.NA, "": pd.NA, "x": pd.NA, "X": pd.NA}
    )
    return pd.to_numeric(normalized, errors="coerce")


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def dataframe_to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, sheet_df in sheets.items():
            safe_name = name[:31]
            sheet_df.to_excel(writer, sheet_name=safe_name, index=False)
    return output.getvalue()
