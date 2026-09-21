import pandas as pd

from src.interactivity import (
    age_source,
    female_responsibility_source,
    population_source,
    racial_source,
    responsible_race_source,
)


def _model():
    names = [
        "bairro",
        "race_population",
        "race_sex",
        "race_age",
        "demo_age",
        "demo_age_sex",
        "responsible_race",
        "responsible_race_sex",
        "responsible_race_age",
    ]
    return {name: pd.DataFrame({"source": [name]}) for name in names}


def _filters(sex=False, age=False, race=False):
    return {
        "sexos": ["Feminino"] if sex else [],
        "faixas": ["0 a 14 anos"] if age else [],
        "racas": ["Branca"] if race else [],
    }


def test_age_metrics_choose_fact_that_contains_active_dimension():
    model = _model()
    assert age_source(model, _filters())["source"].iloc[0] == "demo_age"
    assert age_source(model, _filters(sex=True))["source"].iloc[0] == "demo_age_sex"
    assert age_source(model, _filters(race=True))["source"].iloc[0] == "race_age"
    assert age_source(model, _filters(sex=True, race=True)) is None


def test_racial_metrics_choose_fact_that_contains_active_dimension():
    model = _model()
    assert racial_source(model, _filters())["source"].iloc[0] == "race_population"
    assert racial_source(model, _filters(sex=True))["source"].iloc[0] == "race_sex"
    assert racial_source(model, _filters(age=True))["source"].iloc[0] == "race_age"
    assert racial_source(model, _filters(sex=True, age=True)) is None


def test_population_uses_joint_fact_and_rejects_unpublished_three_way_cross():
    model = _model()
    assert population_source(model, _filters(sex=True, age=True))["source"].iloc[0] == "demo_age_sex"
    assert population_source(model, _filters(sex=True, race=True))["source"].iloc[0] == "race_sex"
    assert population_source(model, _filters(age=True, race=True))["source"].iloc[0] == "race_age"
    assert population_source(model, _filters(sex=True, age=True, race=True)) is None


def test_responsible_metrics_do_not_ignore_unsupported_age_filter():
    model = _model()
    assert female_responsibility_source(model, _filters(age=True)) is None
    assert responsible_race_source(model, _filters(age=True)) is None
    assert responsible_race_source(model, _filters(sex=True))["source"].iloc[0] == "responsible_race_sex"
