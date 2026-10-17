from __future__ import annotations

import pandas as pd
import numpy as np
import streamlit as st

from src import charts, metrics
from src.data_cleaning import clean_raw_tables, detect_inconsistencies
from src.data_loader import (
    load_dictionary,
    load_processed_audit_tables,
    load_processed_model,
    load_raw_tables,
    processed_model_available,
)
from src.exports import csv_bytes, excel_report, pdf_insights
from src.filters import filter_frame, sorted_options
from src.insights import all_insights
from src.interactivity import (
    age_source,
    female_responsibility_source,
    population_source,
    racial_source,
    responsible_race_source,
    unavailable_reason,
)
from src.maps import build_choropleth, build_point_map
from src.modeling import build_model
from src.presentation import (
    formatted_display_frame,
    get_metric_help,
    get_display_name,
    presentation_frame,
)
from src.utils import br_number, br_percent


st.set_page_config(
    page_title="Análises do Censo 2022",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #edf2f7;
        --muted: #aab6c4;
        --surface: #121a23;
        --surface-soft: #171f29;
        --line: #293542;
        --accent: #64899b;
    }
    .stApp { background: #0b1015; color: var(--ink); }
    [data-testid="stSidebar"] {
        background: #111820;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0.15rem !important; }
    [data-testid="stSidebar"] h1 {
        font-size: 1.4rem !important;
        line-height: 1.2 !important;
        margin: 0 0 0.15rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { margin-top: 0; margin-bottom: 0.35rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 0; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.2rem 0.55rem;
        border-radius: 0.45rem;
        border-left: 3px solid transparent;
        font-size: 0.94rem;
        transition: background-color 120ms ease, border-color 120ms ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #19232e; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: #1a2631;
        border-left-color: var(--accent);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 0.6rem;
        background: #131b24;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary { padding-top: 0.55rem; padding-bottom: 0.55rem; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] { margin-bottom: 0.35rem; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="combobox"] {
        min-height: 2.45rem;
        border-radius: 0.55rem;
    }
    .block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1500px; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
    h1 { font-size: clamp(1.8rem, 2.5vw, 2.35rem) !important; margin-bottom: 0.2rem !important; }
    h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.08rem !important; }
    .page-intro { color: var(--muted); margin: 0 0 1.35rem; font-size: 0.95rem; }
    .st-key-page-filter-bar {
        margin: 0.8rem 0 1.15rem;
        padding: 0.8rem 1rem 0.55rem;
        border: 1px solid var(--line);
        border-radius: 0.6rem;
        background: #121a23;
    }
    .st-key-page-filter-bar [data-testid="stCaptionContainer"] { margin-bottom: 0.15rem; }
    .st-key-page-filter-bar [data-testid="stRadio"] p,
    .st-key-page-filter-bar [data-testid="stSelectbox"] label { color: var(--muted); }
    [data-testid="stHorizontalBlock"] { gap: 1rem; align-items: stretch; }
    .st-key-kpi-info-população-analisada,
    .st-key-kpi-info-municípios,
    .st-key-kpi-info-bairros,
    .st-key-kpi-info-IDR_MEDIO,
    .st-key-kpi-positive-REPRESENTATIVIDADE_FEMININA,
    .st-key-kpi-warning-JOVENS,
    .st-key-kpi-warning-IDOSOS { height: 100%; }
    div[data-testid="stMetric"] {
        box-sizing: border-box;
        min-height: 136px;
        height: 136px;
        padding: 1rem 1.05rem;
        border: 1px solid var(--line);
        border-left: 4px solid var(--accent);
        border-radius: 0.65rem;
        background: var(--surface);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.14);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.35;
        min-height: 2.7em;
        max-height: 2.7em;
        overflow: hidden;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--ink);
        font-size: clamp(1.25rem, 1.7vw, 1.7rem);
        line-height: 1.2;
        white-space: nowrap;
    }
    .st-key-kpi-positive div[data-testid="stMetric"],
    .st-key-kpi-warning div[data-testid="stMetric"],
    .st-key-kpi-danger div[data-testid="stMetric"] { border-left-color: var(--accent); }
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 0.65rem;
        background: var(--surface);
        overflow: hidden;
    }
    [data-testid="stDataFrame"] { padding: 0.15rem; }
    [data-testid="stPlotlyChart"] { padding: 0.3rem; }
    [data-testid="stSelectbox"], [data-testid="stRadio"], [data-testid="stMultiSelect"] { color: var(--ink); }
    [data-testid="stTextInput"] input, [data-testid="stSelectbox"] [role="combobox"],
    [data-testid="stMultiSelect"] [role="combobox"] {
        background: #151e28;
        border-color: #344251;
        border-radius: 0.45rem;
    }
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
        border-radius: 0.45rem;
        font-weight: 600;
        min-height: 2.6rem;
    }
    :focus-visible { outline: 2px solid #83a9bb !important; outline-offset: 2px; }
    .note {
        display: block;
        margin: 0 0 1rem !important;
        border: 1px solid var(--line);
        border-left: 4px solid var(--accent);
        border-radius: 0.55rem;
        background: var(--surface);
        padding: 14px 16px;
        color: var(--ink);
        line-height: 1.6;
    }
    @media (max-width: 768px) {
        .block-container { padding: 1.2rem 1rem 2rem; }
        [data-testid="stHorizontalBlock"] { gap: 0.7rem; }
        div[data-testid="stMetric"] { min-height: 120px; height: 120px; padding: 0.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Carregando e tratando dados censitários...")
def load_project():
    if processed_model_available():
        model = load_processed_model()
        treatment_log, profile, inconsistencies = load_processed_audit_tables()
        dictionary = load_dictionary()
        return model, treatment_log, profile, inconsistencies, dictionary
    raw = load_raw_tables()
    cleaned, treatment_log, profile = clean_raw_tables(raw)
    model = build_model(cleaned)
    inconsistencies = detect_inconsistencies(model)
    dictionary = load_dictionary()
    return model, treatment_log, profile, inconsistencies, dictionary


def metric_card(label: str, value: str, metric_key: str | None = None, tone: str = "info"):
    """Render a consistent KPI with an optional native accessible tooltip."""
    card_key = metric_key or label.casefold().replace(" ", "-")
    with st.container(key=f"kpi-{tone}-{card_key}"):
        st.metric(label, value, help=get_metric_help(metric_key) if metric_key else None, border=True)


def display_dataframe(df: pd.DataFrame, **kwargs):
    st.dataframe(formatted_display_frame(df), **kwargs)


PAGE_DESCRIPTIONS = {
    "Visão Geral": "Indicadores principais e uma leitura rápida da população no recorte selecionado.",
    "Municípios": "Compare os municípios e explore seus indicadores e bairros.",
    "Bairros": "Consulte os indicadores e rankings dos bairros disponíveis.",
    "Demografia": "Explore a distribuição da população por idade e sexo.",
    "Domicílios": "Explore a quantidade de domicílios, moradores por domicílio e imputações nas informações domiciliares.",
    "Território e Densidade": "Compare a concentração populacional por área nos municípios e bairros disponíveis.",
    "Diversidade Racial": "Analise a composição racial e a diversidade entre territórios.",
    "Responsáveis pelo Domicílio": "Conheça o perfil das pessoas responsáveis pelos domicílios.",
    "Mapa": "Visualize indicadores por bairro usando as referências geográficas disponíveis.",
    "Análises e Narrativa": "As análises são recalculadas automaticamente conforme os filtros de UF, município, bairro, sexo, faixa etária e cor ou raça.",
    "Qualidade dos Dados": "Consulte o perfil, os tratamentos e as validações das bases.",
    "Exportação": "Baixe os dados e relatórios disponíveis para análise.",
    "Sobre o Projeto": "Conheça as fontes, escolhas metodológicas e escopo desta aplicação.",
}


def page_header(title: str, include_description: bool = True):
    st.title(title)
    if include_description:
        page_description(title)


def page_description(title: str):
    description = PAGE_DESCRIPTIONS.get(title)
    if description:
        st.markdown(f"<p class='page-intro'>{description}</p>", unsafe_allow_html=True)


def page_filter_bar():
    """Return a consistently styled strip for page-specific controls."""
    return st.container(key="page-filter-bar")


def story_scope(model: dict[str, pd.DataFrame], filtros: dict) -> str:
    """Describe the active dashboard slice with names rather than geographic codes."""
    parts = []
    bairro = model.get("bairro", pd.DataFrame())
    if filtros.get("municipios"):
        names = bairro.loc[bairro["CD_MUN"].astype("string").isin(filtros["municipios"]), "NM_MUN"].dropna().unique()
        parts.append("Município: " + ", ".join(map(str, names)))
    if filtros.get("bairros"):
        names = bairro.loc[bairro["CD_BAIRRO"].astype("string").isin(filtros["bairros"]), "NM_BAIRRO"].dropna().unique()
        parts.append("Bairro: " + ", ".join(map(str, names)))
    for key, label in [("racas", "Cor ou raça"), ("faixas", "Faixa etária"), ("sexos", "Sexo")]:
        if filtros.get(key):
            parts.append(f"{label}: " + ", ".join(map(str, filtros[key])))
    return " · ".join(parts) if parts else "Todos os territórios e grupos disponíveis"


def merge_percentage_metric(table, source, group_cols, calculator, output_name):
    """Merge an interactive percentage or mark it unavailable without inventing data."""
    if source is None:
        result = table.copy()
        result[output_name] = np.nan
        return result
    calculated = calculator(source, group_cols)
    return table.merge(
        calculated[group_cols + ["Percentual"]].rename(columns={"Percentual": output_name}),
        on=group_cols,
        how="left",
        validate="one_to_one",
    )


def merge_population_metric(table, source, group_cols):
    result = table.drop(columns=["Populacao"], errors="ignore")
    if source is None:
        result["Populacao"] = np.nan
        return result
    population = (
        source.groupby(group_cols, dropna=False, observed=True)["valor"]
        .sum(min_count=1)
        .rename("Populacao")
        .reset_index()
    )
    return result.merge(population, on=group_cols, how="left", validate="one_to_one")


def filtered_model(model: dict[str, pd.DataFrame], filtros: dict) -> dict[str, pd.DataFrame]:
    return {
        name: filter_frame(
            df,
            ufs=filtros["ufs"],
            municipios=filtros["municipios"],
            bairros=filtros["bairros"],
            sexos=filtros["sexos"],
            faixas=filtros["faixas"],
            racas=filtros["racas"],
        )
        for name, df in model.items()
    }


def sidebar_filters(model: dict[str, pd.DataFrame]) -> dict:
    bairro = model["bairro"]
    st.sidebar.title("Censo 2022")
    st.sidebar.caption("Análises territoriais · IBGE")
    st.sidebar.markdown("**Navegação**")
    page = st.sidebar.radio(
        "Página",
        [
            "Visão Geral",
            "Municípios",
            "Bairros",
            "Demografia",
            "Domicílios",
            "Território e Densidade",
            "Diversidade Racial",
            "Responsáveis",
            "Mapa",
            "Análises e Narrativa",
            "Qualidade dos Dados",
            "Exportação",
            "Sobre o Projeto",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    with st.sidebar.expander("Filtros do recorte", expanded=True):
        st.caption("Combine os campos para refinar os resultados.")
        uf_labels = bairro.drop_duplicates("CD_UF").set_index("CD_UF")["NM_UF"].astype(str).to_dict()
        ufs = st.multiselect(
            "UF", sorted(uf_labels), format_func=lambda code: f"{uf_labels[code]} ({code})", placeholder="Todas"
        )
        mun_base = bairro[bairro["CD_UF"].astype("string").isin(ufs)] if ufs else bairro
        mun_labels = mun_base.drop_duplicates("CD_MUN").set_index("CD_MUN")["NM_MUN"].astype(str).to_dict()
        municipios = st.multiselect(
            "Município", sorted(mun_labels), format_func=lambda code: f"{mun_labels[code]} ({code})", placeholder="Todos"
        )
        bairro_base = mun_base[mun_base["CD_MUN"].astype("string").isin(municipios)] if municipios else mun_base
        bairro_labels = {
            str(row.CD_BAIRRO): f"{row.NM_BAIRRO} — {row.NM_MUN} ({row.CD_BAIRRO})"
            for row in bairro_base.itertuples()
        }
        bairros = st.multiselect(
            "Bairro", sorted(bairro_labels), format_func=lambda code: bairro_labels[code], placeholder="Todos"
        )
        sexos = st.multiselect("Sexo", ["Masculino", "Feminino"], placeholder="Todos")
        faixas = st.multiselect(
            "Faixa etária", ["0 a 14 anos", "15 a 29 anos", "30 a 59 anos", "60 anos ou mais"], placeholder="Todas"
        )
        racas = st.multiselect(
            "Cor ou raça", ["Branca", "Preta", "Amarela", "Parda", "Indigena"], placeholder="Todas"
        )
    return {"ufs": ufs, "municipios": municipios, "bairros": bairros, "sexos": sexos, "faixas": faixas, "racas": racas, "page": page}


def summary_kpis(model: dict[str, pd.DataFrame], filtros: dict | None = None) -> dict[str, float]:
    filtros = filtros or {}
    population_data = population_source(model, filtros)
    pop = population_data["valor"].sum(min_count=1) if population_data is not None else np.nan
    race_data = racial_source(model, filtros)
    age_data = age_source(model, filtros)
    responsibility_data = female_responsibility_source(model, filtros)
    idr_bairro = (
        metrics.calcular_idr(race_data, "bairro")
        if race_data is not None and not race_data.empty
        else pd.DataFrame()
    )
    rep = (
        metrics.representatividade_feminina(responsibility_data)
        if responsibility_data is not None
        else pd.DataFrame()
    )
    jovens = metrics.proporcao_jovens(age_data) if age_data is not None else pd.DataFrame()
    idosos = metrics.proporcao_idosos(age_data) if age_data is not None else pd.DataFrame()
    return {
        "Populacao total": pop,
        "Municipios": model["bairro"]["CD_MUN"].nunique(),
        "Bairros": model["bairro"]["CD_BAIRRO"].nunique(),
        "IDR medio": idr_bairro["IDR"].mean() if not idr_bairro.empty else np.nan,
        "Representatividade feminina": rep["Percentual"].iloc[0] if not rep.empty else np.nan,
        "Jovens": jovens["Percentual"].iloc[0] if not jovens.empty else np.nan,
        "Idosos": idosos["Percentual"].iloc[0] if not idosos.empty else np.nan,
    }


def page_overview(model, filtros):
    page_header("Visão Geral", include_description=False)
    with page_filter_bar():
        st.caption("Filtros desta visualização")
        mode = st.radio("Distribuição racial", ["Quantidade", "Percentual"], horizontal=True)
    page_description("Visão Geral")
    unavailable_metrics = []
    if racial_source(model, filtros) is None:
        unavailable_metrics.append("diversidade e composição racial")
    if age_source(model, filtros) is None:
        unavailable_metrics.append("população jovem e idosa")
    if female_responsibility_source(model, filtros) is None:
        unavailable_metrics.append("responsáveis do sexo feminino")
    if unavailable_metrics:
        st.warning(
            f"{unavailable_reason(filtros)} Métricas afetadas: "
            + ", ".join(unavailable_metrics)
            + "."
        )
    k = summary_kpis(model, filtros)
    cols = st.columns(4, gap="large")
    with cols[0]:
        metric_card("População Analisada", br_number(k["Populacao total"]))
    with cols[1]:
        metric_card("Municípios", br_number(k["Municipios"]))
    with cols[2]:
        metric_card("Bairros", br_number(k["Bairros"]))
    with cols[3]:
        metric_card(
            "Índice de Diversidade Racial Médio",
            br_number(k["IDR medio"], 2),
            "IDR_MEDIO",
        )
    cols = st.columns(4, gap="large")
    with cols[0]:
        metric_card(
            "Responsáveis do Sexo Feminino",
            br_percent(k["Representatividade feminina"]),
            "REPRESENTATIVIDADE_FEMININA",
            "positive",
        )
    with cols[1]:
        metric_card("População Jovem", br_percent(k["Jovens"]), "JOVENS", "warning")
    with cols[2]:
        metric_card("População Idosa", br_percent(k["Idosos"]), "IDOSOS", "warning")
    col1, col2 = st.columns([1.1, 1])
    with col1:
        race_data = racial_source(model, filtros)
        if race_data is None:
            st.info(unavailable_reason(filtros))
        else:
            st.plotly_chart(charts.bar_distribution(race_data, "Cor_Raca", percent=mode == "Percentual", title="Composição Racial da População"), width="stretch")
    with col2:
        if filtros.get("racas"):
            st.info(
                "A pirâmide etária por sexo fica indisponível com o filtro de cor ou raça, "
                "pois a base não possui o cruzamento simultâneo entre idade, sexo e raça."
            )
        else:
            st.plotly_chart(charts.age_pyramid(model["demo_age_sex"]), width="stretch")


def page_municipios(model, filtros):
    page_header("Municípios", include_description=False)
    with page_filter_bar():
        st.caption("Filtros desta visualização")
        selected = st.selectbox(
            "Ver bairros de um município",
            [""] + sorted_options(model["bairro"]["NM_MUN"]),
            format_func=lambda value: value or "Todos os municípios",
        )
    page_description("Municípios")
    race_data = racial_source(model, filtros)
    age_data = age_source(model, filtros)
    responsibility_data = female_responsibility_source(model, filtros)
    if race_data is None:
        table = model["bairro"][["CD_MUN", "NM_MUN"]].drop_duplicates().rename(columns={"NM_MUN": "Municipio"})
        table[["Populacao", "IDR", "Grupo racial predominante"]] = np.nan
        st.info(unavailable_reason(filtros))
    else:
        table = metrics.ranking_municipios_diversidade(race_data)
        st.plotly_chart(charts.horizontal_ranking(table, "Municipio", "IDR", "Municípios com Maior Diversidade Racial"), width="stretch")
    table = merge_population_metric(table, population_source(model, filtros), ["CD_MUN"])
    table = merge_percentage_metric(table, responsibility_data, ["CD_MUN"], metrics.representatividade_feminina, "Representatividade feminina")
    table = merge_percentage_metric(table, age_data, ["CD_MUN"], metrics.proporcao_jovens, "Jovens")
    table = merge_percentage_metric(table, age_data, ["CD_MUN"], metrics.proporcao_idosos, "Idosos")
    display_dataframe(
        presentation_frame(
            table,
            ["Posicao", "Municipio", "Populacao", "IDR", "Grupo racial predominante", "Representatividade feminina", "Jovens", "Idosos"],
        ),
        width="stretch",
        hide_index=True,
    )
    if selected:
        bairros = model["bairro"][model["bairro"]["NM_MUN"].eq(selected)].sort_values("populacao_total", ascending=False)
        display_dataframe(
            presentation_frame(bairros, ["NM_BAIRRO", "NM_MUN", "populacao_total", "AREA_KM2"]),
            width="stretch",
            hide_index=True,
        )


def page_bairros(model, filtros):
    page_header("Bairros")
    group_cols = ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"]
    race_data = racial_source(model, filtros)
    age_data = age_source(model, filtros)
    responsibility_data = female_responsibility_source(model, filtros)
    if race_data is None:
        table = model["bairro"][group_cols].drop_duplicates()
        table[["Populacao", "IDR"]] = np.nan
        st.info(unavailable_reason(filtros))
    else:
        table = metrics.calcular_idr(race_data, "bairro")
        st.plotly_chart(charts.horizontal_ranking(table, "NM_BAIRRO", "Populacao", "Bairros Mais Populosos"), width="stretch")
    table = merge_population_metric(table, population_source(model, filtros), group_cols)
    table = merge_percentage_metric(table, responsibility_data, group_cols, metrics.representatividade_feminina, "Representatividade feminina")
    table = merge_percentage_metric(table, age_data, group_cols, metrics.proporcao_jovens, "Jovens")
    table = merge_percentage_metric(table, age_data, group_cols, metrics.proporcao_idosos, "Idosos")
    display_dataframe(
        presentation_frame(
            table,
            ["NM_BAIRRO", "NM_MUN", "Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"],
        ),
        width="stretch",
        hide_index=True,
    )


def page_demography(model, filtros):
    page_header("Demografia")
    col1, col2 = st.columns(2)
    with col1:
        if filtros.get("racas"):
            st.info("Pirâmide indisponível: não há cruzamento simultâneo entre idade, sexo e raça.")
        else:
            st.plotly_chart(charts.age_pyramid(model["demo_age_sex"], "Pirâmide Etária por Sexo"), width="stretch")
    with col2:
        if filtros.get("sexos"):
            st.info("Distribuição por idade e raça indisponível com filtro de sexo.")
        else:
            st.plotly_chart(charts.line_or_bar_age_by_race(model["race_age"]), width="stretch")
    age = (
        model["demo_age"]
        .groupby("Faixa_Etaria", dropna=False, observed=True)["valor"]
        .sum()
        .reset_index()
    )
    display_dataframe(presentation_frame(age), width="stretch", hide_index=True)


def page_households(model, filtros):
    page_header("Domicílios")
    if filtros.get("sexos") or filtros.get("faixas") or filtros.get("racas"):
        st.info(
            "Os indicadores domiciliares usam a tabela básica e não variam com filtros "
            "de sexo, faixa etária ou cor/raça."
        )

    bairro = model["bairro"]
    if bairro.empty:
        st.info("Não há dados para os filtros territoriais selecionados.")
        return
    summary = metrics.household_summary(bairro).iloc[0]
    cols = st.columns(4, gap="large")
    with cols[0]:
        metric_card("Domicílios", br_number(summary["Domicilios"]))
    with cols[1]:
        metric_card("Domicílios Ocupados", br_number(summary["Domicilios_Ocupados"]))
    with cols[2]:
        metric_card(
            "Moradores por Domicílio Ocupado",
            br_number(summary["Media_Moradores"], 1),
        )
    with cols[3]:
        metric_card(
            "Domicílios com Valor Imputado",
            br_percent(summary["DPO_Imputados"]),
        )

    st.caption(
        "Médias e percentuais são ponderados pelo número de domicílios ocupados; "
        "o percentual de imputação descreve a informação de moradores dos domicílios."
    )
    by_neighborhood = metrics.household_summary(
        bairro, ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"]
    ).sort_values("Domicilios_Ocupados", ascending=False)
    by_neighborhood["Territorio"] = (
        by_neighborhood["NM_BAIRRO"].astype(str)
        + " — "
        + by_neighborhood["NM_MUN"].astype(str)
    )
    st.plotly_chart(
        charts.horizontal_ranking(
            by_neighborhood,
            "Territorio",
            "Domicilios_Ocupados",
            "Bairros com Mais Domicílios Ocupados",
        ),
        width="stretch",
    )
    st.subheader("Perfil por Bairro")
    display_dataframe(
        presentation_frame(
            by_neighborhood.head(100),
            [
                "NM_BAIRRO",
                "NM_MUN",
                "Domicilios",
                "Domicilios_Ocupados",
                "Media_Moradores",
                "DPO_Imputados",
            ],
        ),
        width="stretch",
        hide_index=True,
    )


def page_territory(model, filtros):
    page_header("Território e Densidade")
    if filtros.get("sexos") or filtros.get("faixas") or filtros.get("racas"):
        st.info(
            "A densidade usa a população total da tabela básica e não varia com filtros "
            "de sexo, faixa etária ou cor/raça."
        )

    bairro = model["bairro"]
    if bairro.empty:
        st.info("Não há dados para os filtros territoriais selecionados.")
        return
    overall_density = metrics.population_density(bairro)
    if overall_density.empty:
        st.info("Não há população e área válidas em conjunto para calcular densidade.")
        return
    overall = overall_density.iloc[0]
    neighborhood_density = metrics.population_density(
        bairro, ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"]
    )
    valid_density = neighborhood_density.dropna(subset=["Densidade"])
    cols = st.columns(3, gap="large")
    with cols[0]:
        metric_card("Bairros com Área Válida", br_number(len(valid_density)))
    with cols[1]:
        metric_card("Área Total (km²)", br_number(overall["AREA_KM2"], 1))
    with cols[2]:
        metric_card(
            "Densidade do Recorte",
            f"{br_number(overall['Densidade'], 1)} hab./km²",
        )

    st.caption(
        "Densidade = população residente da tabela básica ÷ área em km². "
        "O indicador agregado usa a soma da população e das áreas dos bairros com valores "
        "válidos e área positiva; esses bairros são os únicos incluídos no ranking."
    )
    municipality_density = metrics.population_density(
        bairro, ["CD_MUN", "NM_MUN"]
    ).sort_values("Densidade", ascending=False)
    valid_density = valid_density.copy()
    valid_density["Territorio"] = (
        valid_density["NM_BAIRRO"].astype(str)
        + " — "
        + valid_density["NM_MUN"].astype(str)
    )
    cols = st.columns(2)
    with cols[0]:
        if valid_density.empty:
            st.info("Não há bairros com área válida para calcular densidade.")
        else:
            st.plotly_chart(
                charts.horizontal_ranking(
                    valid_density,
                    "Territorio",
                    "Densidade",
                    "Bairros Mais Densos",
                ),
                width="stretch",
            )
    with cols[1]:
        municipality_density = municipality_density.dropna(subset=["Densidade"])
        if municipality_density.empty:
            st.info("Não há municípios com área válida para calcular densidade.")
        else:
            st.plotly_chart(
                charts.horizontal_ranking(
                    municipality_density,
                    "NM_MUN",
                    "Densidade",
                    "Municípios Mais Densos",
                ),
                width="stretch",
            )
    st.subheader("Bairros por Densidade")
    display_dataframe(
        presentation_frame(
            valid_density.sort_values("Densidade", ascending=False).head(100),
            ["NM_BAIRRO", "NM_MUN", "Populacao", "AREA_KM2", "Densidade"],
        ),
        width="stretch",
        hide_index=True,
    )


def page_diversity(model, filtros):
    page_header("Diversidade Racial")
    race_data = racial_source(model, filtros)
    if race_data is None:
        st.warning(unavailable_reason(filtros))
        return
    idr_bairro = metrics.calcular_idr(race_data, "bairro")
    idr_mun = metrics.calcular_idr(race_data, "municipio")
    col1, col2 = st.columns(2)
    with col1:
        population_bands = charts.population_diversity_by_band(idr_bairro)
        if population_bands is None:
            st.info("Não há dados válidos de população e diversidade racial para exibir neste gráfico.")
        else:
            st.plotly_chart(population_bands, width="stretch")
            st.caption(
                "Cada barra mostra o IDR médio dos bairros daquela faixa populacional. "
                "O número de bairros está indicado acima da barra; é uma comparação descritiva, não causal."
            )
    with col2:
        st.plotly_chart(charts.bar_distribution(race_data, "Cor_Raca", percent=True, title="Composição Racial da População"), width="stretch")
    st.subheader("Municípios com Maior Diversidade Racial", help=get_metric_help("IDR"))
    display_dataframe(
        presentation_frame(idr_mun, ["NM_MUN", "Populacao", "IDR"]),
        width="stretch",
        hide_index=True,
    )


def page_responsibles(model, filtros):
    page_header("Responsáveis pelo Domicílio")
    responsibility_data = female_responsibility_source(model, filtros)
    race_data = responsible_race_source(model, filtros)
    rep = metrics.representatividade_feminina(responsibility_data, ["Cor_Raca"]) if responsibility_data is not None else pd.DataFrame()
    indig = metrics.ranking_responsaveis_indigenas_40mais(model["responsible_race_age"]) if not filtros.get("sexos") and not filtros.get("faixas") else pd.DataFrame()
    col1, col2 = st.columns(2)
    with col1:
        if filtros.get("faixas"):
            st.info("Distribuição por sexo indisponível com filtro de idade.")
        else:
            st.plotly_chart(charts.bar_distribution(model["responsible_race_sex"], "Sexo", title="Responsáveis por Sexo"), width="stretch")
    with col2:
        if race_data is None:
            st.info(unavailable_reason(filtros))
        else:
            st.plotly_chart(charts.bar_distribution(race_data, "Cor_Raca", title="Responsáveis por Cor ou Raça"), width="stretch")
    st.subheader("Participação Feminina entre Responsáveis")
    if rep.empty:
        st.info("Indicador indisponível com filtro de idade: não há cruzamento entre idade e sexo dos responsáveis.")
    else:
        display_dataframe(presentation_frame(rep), width="stretch", hide_index=True)
    st.subheader("Responsáveis Indígenas com 40 Anos ou Mais")
    if indig.empty:
        st.info("Indicador indisponível para os filtros selecionados porque as faixas publicadas para responsáveis não permitem esse cruzamento exato.")
    else:
        display_dataframe(
            presentation_frame(indig, ["NM_BAIRRO", "NM_MUN", "Quantidade", "Total_Responsaveis", "Percentual"]),
            width="stretch",
            hide_index=True,
        )


def page_map(model, filtros):
    page_header("Mapa", include_description=False)
    race_data = racial_source(model, filtros)
    age_data = age_source(model, filtros)
    responsibility_data = female_responsibility_source(model, filtros)
    idr = metrics.calcular_idr(race_data, "bairro") if race_data is not None else pd.DataFrame()
    rep = metrics.representatividade_feminina(responsibility_data, ["CD_BAIRRO"]) if responsibility_data is not None else pd.DataFrame()
    jovens = metrics.proporcao_jovens(age_data, ["CD_BAIRRO"]) if age_data is not None else pd.DataFrame()
    idosos = metrics.proporcao_idosos(age_data, ["CD_BAIRRO"]) if age_data is not None else pd.DataFrame()
    indicator_columns = ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"]
    if "NM_UF" in model["bairro"].columns:
        indicator_columns.insert(3, "NM_UF")
    indicators = model["bairro"][indicator_columns].drop_duplicates("CD_BAIRRO")
    indicators = merge_population_metric(indicators, population_source(model, filtros), ["CD_BAIRRO"])
    for frame, source_column, output_column in [
        (idr, "IDR", "IDR"),
        (rep, "Percentual", "Representatividade feminina"),
        (jovens, "Percentual", "Jovens"),
        (idosos, "Percentual", "Idosos"),
    ]:
        if frame.empty:
            indicators[output_column] = np.nan
        else:
            indicators = indicators.merge(
                frame[["CD_BAIRRO", source_column]].rename(columns={source_column: output_column}),
                on="CD_BAIRRO",
                how="left",
                validate="one_to_one",
            )
    indicator_options = [
        column
        for column in ["Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"]
        if indicators[column].notna().any()
    ]
    if not indicator_options:
        st.warning(unavailable_reason(filtros))
        return
    with page_filter_bar():
        st.caption("Filtros desta visualização")
        control_cols = st.columns([1, 2])
        with control_cols[0]:
            indicator = st.selectbox(
                "Indicador",
                indicator_options,
                format_func=get_display_name,
                help=get_metric_help("IDR"),
            )
        with control_cols[1]:
            map_mode = st.radio(
                "Cobertura geográfica",
                ["Brasil — pontos representativos", "Bahia — limites oficiais"],
                horizontal=True,
            )
    page_description("Mapa")
    if map_mode == "Brasil — pontos representativos":
        fig = build_point_map(indicators, indicator)
        empty_message = "Não há coordenadas disponíveis para os filtros selecionados."
        st.caption(
            "Cada ponto fica dentro do polígono oficial do bairro no Censo 2022. "
            "Os pontos representam localização, não o tamanho ou o limite territorial."
        )
    else:
        fig = build_choropleth(indicators, indicator)
        empty_message = (
            "Não há malha geográfica disponível para os filtros selecionados. "
            "A visualização de limites detalhados está disponível para bairros da Bahia."
        )
    if fig is None:
        st.info(empty_message)
    else:
        st.plotly_chart(fig, width="stretch")


def page_quality(profile, treatment_log, inconsistencies, dictionary):
    page_header("Qualidade dos Dados")
    st.subheader("Perfil das Tabelas")
    display_dataframe(presentation_frame(profile), width="stretch", hide_index=True)
    st.subheader("Tratamentos Registrados")
    display_dataframe(presentation_frame(treatment_log), width="stretch", hide_index=True)
    st.subheader("Validações")
    display_dataframe(presentation_frame(inconsistencies), width="stretch", hide_index=True)
    st.subheader("Dicionário de Dados")
    display_dataframe(
        presentation_frame(dictionary.head(300), hidden=["variavel_norm"]),
        width="stretch",
        hide_index=True,
    )


def page_exports(model, filtros):
    page_header("Exportação")
    idr_mun = metrics.ranking_municipios_diversidade(model["race_population"])
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro")
    insights = all_insights(model, filtros)
    sheets = {
        "Resumo": presentation_frame(pd.DataFrame([summary_kpis(model, filtros)])),
        "Municípios": presentation_frame(idr_mun),
        "Bairros": presentation_frame(idr_bairro),
        "Cor ou Raça": presentation_frame(model["race_population"]),
        "Sexo": presentation_frame(model["demo_age_sex"]),
        "Faixa Etária": presentation_frame(model["demo_age"]),
        "Responsáveis": presentation_frame(model["responsible_race_sex"]),
    }
    csv_columns = [
        "CD_BAIRRO", "NM_BAIRRO", "CD_MUN", "NM_MUN", "CD_UF", "NM_UF",
        "populacao_total", "domicilios_total", "domicilios_ocupados", "AREA_KM2",
    ]
    st.download_button(
        "Baixar dados filtrados em CSV",
        csv_bytes(presentation_frame(model["bairro"], csv_columns)),
        "dados_filtrados.csv",
        "text/csv",
    )
    st.download_button("Baixar relatório Excel", excel_report(sheets), "relatorio_analises.xlsx")
    st.download_button("Baixar análises em PDF", pdf_insights("Análises do Censo 2022", insights), "analises.pdf", "application/pdf")


def page_storytelling(model, filtros):
    page_header("Análises e Narrativa")
    st.markdown(
        f"<div class='note'><strong>Recorte aplicado:</strong> {story_scope(model, filtros)}</div>",
        unsafe_allow_html=True,
    )
    insights = all_insights(model, filtros)
    if not insights:
        st.info("Não há dados suficientes para gerar análises para o recorte atual.")
    for insight in insights:
        st.markdown(f"<div class='note'>{insight}</div>", unsafe_allow_html=True)


def page_about():
    page_header("Sobre o Projeto")
    st.markdown(
        """
        Projeto analítico em Python para os agregados do Censo 2022 por bairros.

        **Desenvolvido por Emanuel Sousa Vasconcellos Lima.**

        A modelagem utiliza o Código do Bairro como chave territorial, preserva os arquivos originais e cria conjuntos analíticos para população por idade, sexo, cor ou raça e características dos responsáveis pelos domicílios.

        O Índice de Diversidade Racial (IDR) utiliza o índice de Simpson normalizado, reescalado para o intervalo de 0 a 1 conforme o número de grupos raciais observados. Como não há uma fórmula oficial de IDR nos arquivos fornecidos, a decisão metodológica está documentada no código e no projeto.

        A idade média dos responsáveis é estimada pelos pontos médios das faixas etárias. Classes abertas utilizam um ponto médio metodológico documentado, sem atribuir idades individuais inexistentes.

        O mapa nacional utiliza pontos representativos calculados dentro dos polígonos oficiais dos bairros. Para a Bahia, também está disponível a visualização dos limites territoriais detalhados.

        **Licença:** este projeto é distribuído sob a Licença MIT. Consulte o arquivo `LICENSE` para conhecer os termos.
        """
    )


def main():
    model, treatment_log, profile, inconsistencies, dictionary = load_project()
    filtros = sidebar_filters(model)
    current = filtered_model(model, filtros)
    page = filtros["page"]
    if page == "Visão Geral":
        page_overview(current, filtros)
    elif page == "Municípios":
        page_municipios(current, filtros)
    elif page == "Bairros":
        page_bairros(current, filtros)
    elif page == "Demografia":
        page_demography(current, filtros)
    elif page == "Domicílios":
        page_households(current, filtros)
    elif page == "Território e Densidade":
        page_territory(current, filtros)
    elif page == "Diversidade Racial":
        page_diversity(current, filtros)
    elif page == "Responsáveis":
        page_responsibles(current, filtros)
    elif page == "Mapa":
        page_map(current, filtros)
    elif page == "Análises e Narrativa":
        page_storytelling(current, filtros)
    elif page == "Qualidade dos Dados":
        page_quality(profile, treatment_log, inconsistencies, dictionary)
    elif page == "Exportação":
        page_exports(current, filtros)
    else:
        page_about()


if __name__ == "__main__":
    main()
