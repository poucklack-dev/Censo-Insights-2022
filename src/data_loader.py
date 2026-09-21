from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

from . import config

MODEL_TABLES = (
    "bairro",
    "race_population",
    "race_sex",
    "race_age",
    "responsible_race",
    "responsible_race_sex",
    "responsible_race_age",
    "demo_age",
    "demo_age_sex",
)


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


def processed_model_available() -> bool:
    return all(
        (config.PROCESSED_DIR / f"{name}.parquet").exists()
        or (config.PROCESSED_DIR / f"{name}.csv").exists()
        for name in MODEL_TABLES
    )


def load_processed_model() -> dict[str, pd.DataFrame]:
    """Load the compact modeled layer, preferring Parquet when available."""
    model = {}
    for name in MODEL_TABLES:
        parquet_path = config.PROCESSED_DIR / f"{name}.parquet"
        csv_path = config.PROCESSED_DIR / f"{name}.csv"
        if parquet_path.exists():
            model[name] = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            frame = pd.read_csv(
                csv_path,
                sep=";",
                decimal=",",
                dtype={col: "string" for col in ["CD_UF", "CD_MUN", "CD_BAIRRO"]},
                low_memory=False,
            )
            for col in frame.select_dtypes(include=["object", "string"]).columns:
                frame[col] = frame[col].astype("category")
            model[name] = frame
        else:
            raise FileNotFoundError(f"Tabela processada ausente: {name}")
    return model


def load_processed_audit_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def read(name: str) -> pd.DataFrame:
        path = config.PROCESSED_DIR / f"{name}.csv"
        return pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig") if path.exists() else pd.DataFrame()

    return read("treatment_log"), read("data_profile"), read("validations")


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


@lru_cache(maxsize=1)
def load_neighborhood_points() -> pd.DataFrame | None:
    """Load compact official representative points without polygon geometry."""
    if not config.NEIGHBORHOOD_POINTS_FILE.exists():
        return None
    return pd.read_csv(
        config.NEIGHBORHOOD_POINTS_FILE,
        dtype={"CD_BAIRRO": "string"},
    )
