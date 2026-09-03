from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from . import config


def _normalize_column_name(value: object) -> str:
    text = str(value).replace("�", "")
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return text.strip().lower()


def read_excel(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, dtype="string")


def load_raw_tables() -> dict[str, pd.DataFrame]:
    files = {
        "basico": config.BASIC_FILE,
        "cor_raca": config.RACE_FILE,
        "demografia": config.DEMOGRAPHY_FILE,
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Arquivos ausentes: " + ", ".join(missing))
    return {name: read_excel(path) for name, path in files.items()}


def load_dictionary() -> pd.DataFrame:
    if not config.DICTIONARY_FILE.exists():
        return pd.DataFrame()
    frames = []
    xl = pd.ExcelFile(config.DICTIONARY_FILE)
    for sheet in xl.sheet_names:
        df = pd.read_excel(config.DICTIONARY_FILE, sheet_name=sheet)
        df.columns = [_normalize_column_name(col) for col in df.columns]
        df["aba"] = sheet
        frames.append(df)
    dictionary = pd.concat(frames, ignore_index=True)
    variable_col = next((col for col in dictionary.columns if "variavel" in col), None)
    if variable_col:
        dictionary["variavel_norm"] = dictionary[variable_col].astype(str).str.upper()
    return dictionary


def load_geodata():
    if not config.GEO_FILE.exists():
        return None
    try:
        import geopandas as gpd
    except ImportError:
        return None
    gdf = gpd.read_file(config.GEO_FILE)
    if "CD_BAIRRO" in gdf.columns:
        gdf["CD_BAIRRO"] = gdf["CD_BAIRRO"].astype(str)
    return gdf

