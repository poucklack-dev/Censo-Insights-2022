import pandas as pd

from src.presentation import (
    DISPLAY_NAMES,
    METRIC_HELP,
    get_display_name,
    get_metric_help,
    presentation_frame,
)


def test_display_names_cover_territorial_keys_and_idr():
    assert DISPLAY_NAMES["CD_MUN"] == "Código do Município"
    assert DISPLAY_NAMES["NM_MUN"] == "Município"
    assert DISPLAY_NAMES["CD_BAIRRO"] == "Código do Bairro"
    assert DISPLAY_NAMES["NM_BAIRRO"] == "Bairro"
    assert DISPLAY_NAMES["IDR"] == "Índice de Diversidade Racial (IDR)"


def test_presentation_frame_renames_only_display_copy():
    source = pd.DataFrame(
        {
            "CD_BAIRRO": ["1"],
            "NM_BAIRRO": ["Centro"],
            "NM_MUN": ["Cidade"],
            "Populacao": [100],
        }
    )
    displayed = presentation_frame(
        source,
        ["NM_BAIRRO", "NM_MUN", "Populacao"],
    )
    assert list(displayed.columns) == ["Bairro", "Município", "População"]
    assert list(source.columns) == ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN", "Populacao"]


def test_presentation_frame_hides_columns_without_changing_rows():
    source = pd.DataFrame({"NM_BAIRRO": ["A", "B"], "variavel_norm": ["X", "Y"]})
    displayed = presentation_frame(source, hidden=["variavel_norm"])
    assert list(displayed.columns) == ["Bairro"]
    assert len(displayed) == len(source)


def test_unknown_column_gets_readable_fallback():
    assert get_display_name("nova_coluna") == "Nova Coluna"


def test_idr_help_documents_current_normalized_simpson_method():
    help_text = get_metric_help("IDR")
    assert help_text is not None
    assert "Simpson normalizado" in help_text
    assert "0 a 1" in help_text
    assert METRIC_HELP["IDR"]["name"] == "Índice de Diversidade Racial (IDR)"
