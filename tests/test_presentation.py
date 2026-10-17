import pandas as pd

from src.presentation import (
    DISPLAY_NAMES,
    METRIC_HELP,
    formatted_display_frame,
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


def test_display_formatting_preserves_numeric_sorting_and_brazilian_separators():
    source = pd.DataFrame(
        {
            "População": [999, 352_356],
            "IDR": [0.7851212, 0.1],
            "Participação na População (%)": [50.595952, 0.7],
            "Área (km²)": [0.0014555, 12.34567],
        }
    )
    displayed = formatted_display_frame(source)
    assert pd.api.types.is_numeric_dtype(displayed.data["População"])
    assert displayed.data.sort_values("População", ascending=False)["População"].tolist() == [
        352_356,
        999,
    ]
    html = displayed.to_html()
    assert "352.356" in html
    assert "0,79" in html
    assert "50,6%" in html
    assert "0,0015" in html
    assert source.loc[0, "IDR"] == 0.7851212
    assert source.loc[0, "Participação na População (%)"] == 50.595952


def test_unknown_column_gets_readable_fallback():
    assert get_display_name("nova_coluna") == "Nova Coluna"


def test_idr_help_documents_current_normalized_simpson_method():
    help_text = get_metric_help("IDR")
    assert help_text is not None
    assert "Simpson normalizado" in help_text
    assert "0 a 1" in help_text
    assert METRIC_HELP["IDR"]["name"] == "Índice de Diversidade Racial (IDR)"
