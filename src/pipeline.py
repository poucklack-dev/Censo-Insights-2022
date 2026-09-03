from __future__ import annotations

import pandas as pd

from . import config
from .data_cleaning import clean_raw_tables, detect_inconsistencies
from .data_loader import load_raw_tables
from .modeling import build_model


def run_etl(save: bool = True) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = load_raw_tables()
    cleaned, treatment_log, profile = clean_raw_tables(raw)
    model = build_model(cleaned)
    inconsistencies = detect_inconsistencies(model)
    if save:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        for name, df in model.items():
            df.to_csv(config.PROCESSED_DIR / f"{name}.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
        treatment_log.to_csv(config.PROCESSED_DIR / "treatment_log.csv", index=False, sep=";", encoding="utf-8-sig")
        profile.to_csv(config.PROCESSED_DIR / "data_profile.csv", index=False, sep=";", encoding="utf-8-sig")
        inconsistencies.to_csv(config.PROCESSED_DIR / "validations.csv", index=False, sep=";", encoding="utf-8-sig")
    return model, treatment_log, profile, inconsistencies


if __name__ == "__main__":
    run_etl(save=True)

