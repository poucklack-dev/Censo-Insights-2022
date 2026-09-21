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
from src.maps import build_choropleth, build_point_map
from src.modeling import build_model
from src.presentation import get_display_name, get_metric_help, presentation_frame
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
    .stApp { background: #0B1015; color: #EDF2F7; }
    [data-testid="stSidebar"] { background: #111820; border-right: 1px solid #263241; }
    .note {
        border-left: 3px solid #3BA776;
        background: #101820;
        padding: 12px 14px;
        color: #C9D4DF;
    }
    div[data-testid="stDataFrame"] { border: 1px solid #263241; border-radius: 8px; }
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


def metric_card(label: str, value: str, metric_key: str | None = None):
    """Render a consistent KPI with an optional native accessible tooltip."""
    st.metric(label, value, help=get_metric_help(metric_key) if metric_key else None, border=True)


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
    st.sidebar.caption("Agregados por bairros")
    uf_labels = bairro.drop_duplicates("CD_UF").set_index("CD_UF")["NM_UF"].astype(str).to_dict()
    ufs = st.sidebar.multiselect(
        "UF",
        sorted(uf_labels),
        format_func=lambda code: f"{uf_labels[code]} ({code})",
        placeholder="Opções",
    )
    mun_base = bairro[bairro["CD_UF"].astype("string").isin(ufs)] if ufs else bairro
    mun_labels = (
        mun_base.drop_duplicates("CD_MUN").set_index("CD_MUN")["NM_MUN"].astype(str).to_dict()
    )
    municipios = st.sidebar.multiselect(
        "Município",
        sorted(mun_labels),
        format_func=lambda code: f"{mun_labels[code]} ({code})",
        placeholder="Opções",
    )
    bairro_base = (
        mun_base[mun_base["CD_MUN"].astype("string").isin(municipios)] if municipios else mun_base
    )
    bairro_labels = {
        str(row.CD_BAIRRO): f"{row.NM_BAIRRO} — {row.NM_MUN} ({row.CD_BAIRRO})"
        for row in bairro_base.itertuples()
    }
    bairros = st.sidebar.multiselect(
        "Bairro",
        sorted(bairro_labels),
        format_func=lambda code: bairro_labels[code],
        placeholder="Opções",
    )
    sexos = st.sidebar.multiselect(
        "Sexo", ["Masculino", "Feminino"], placeholder="Opções"
    )
    faixas = st.sidebar.multiselect(
        "Faixa etária",
        ["0 a 14 anos", "15 a 29 anos", "30 a 59 anos", "60 anos ou mais"],
        placeholder="Opções",
    )
    racas = st.sidebar.multiselect(
        "Cor ou raça",
        ["Branca", "Preta", "Amarela", "Parda", "Indigena"],
        placeholder="Opções",
    )
    page = st.sidebar.radio(
        "Página",
        [
            "Visão Geral",
            "Municípios",
            "Bairros",
            "Demografia",
            "Diversidade Racial",
            "Responsáveis",
            "Mapa",
            "Análises e Narrativa",
            "Qualidade dos Dados",
            "Exportação",
            "Sobre o Projeto",
        ],
    )
    return {"ufs": ufs, "municipios": municipios, "bairros": bairros, "sexos": sexos, "faixas": faixas, "racas": racas, "page": page}


def summary_kpis(model: dict[str, pd.DataFrame], filtros: dict | None = None) -> dict[str, float]:
    filtros = filtros or {}
    has_sex = bool(filtros.get("sexos"))
    has_age = bool(filtros.get("faixas"))
    has_race = bool(filtros.get("racas"))
    if has_sex and has_age and has_race:
        pop = np.nan
    elif has_sex and has_race:
        pop = model["race_sex"]["valor"].sum()
    elif has_sex and has_age:
        pop = model["demo_age_sex"]["valor"].sum()
    elif has_race and has_age:
        pop = model["race_age"]["valor"].sum()
    elif has_race:
        pop = model["race_population"]["valor"].sum()
    elif has_age:
        pop = model["demo_age"]["valor"].sum()
    elif has_sex:
        pop = model["demo_age_sex"]["valor"].sum()
    else:
        pop = model["bairro"]["populacao_total"].sum()
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro") if not model["race_population"].empty else pd.DataFrame({"IDR": [0]})
    rep = metrics.representatividade_feminina(model["responsible_race_sex"])
    jovens = metrics.proporcao_jovens(model["demo_age"])
    idosos = metrics.proporcao_idosos(model["demo_age"])
    return {
        "Populacao total": pop,
        "Municipios": model["bairro"]["CD_MUN"].nunique(),
        "Bairros": model["bairro"]["CD_BAIRRO"].nunique(),
        "IDR medio": idr_bairro["IDR"].mean(),
        "Representatividade feminina": rep["Percentual"].iloc[0] if not rep.empty else 0,
        "Jovens": jovens["Percentual"].iloc[0] if not jovens.empty else 0,
        "Idosos": idosos["Percentual"].iloc[0] if not idosos.empty else 0,
    }


def page_overview(model, filtros):
    st.title("Visão Geral")
    if filtros.get("sexos") and filtros.get("faixas") and filtros.get("racas"):
        st.warning(
            "Não existe uma tabela publicada com o cruzamento simultâneo entre sexo, idade e "
            "cor ou raça. A população analisada fica indisponível para evitar um resultado enganoso."
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
            br_number(k["IDR medio"], 3),
            "IDR_MEDIO",
        )
    cols = st.columns(3, gap="large")
    with cols[0]:
        metric_card(
            "Responsáveis do Sexo Feminino",
            br_percent(k["Representatividade feminina"]),
            "REPRESENTATIVIDADE_FEMININA",
        )
    with cols[1]:
        metric_card("População Jovem", br_percent(k["Jovens"]), "JOVENS")
    with cols[2]:
        metric_card("População Idosa", br_percent(k["Idosos"]), "IDOSOS")
    col1, col2 = st.columns([1.1, 1])
    with col1:
        mode = st.radio("Distribuição racial", ["Quantidade", "Percentual"], horizontal=True)
        st.plotly_chart(charts.bar_distribution(model["race_population"], "Cor_Raca", percent=mode == "Percentual", title="Composição Racial da População"), width="stretch")
    with col2:
        st.plotly_chart(charts.age_pyramid(model["demo_age_sex"]), width="stretch")


def page_municipios(model):
    st.title("Municípios")
    idr = metrics.ranking_municipios_diversidade(model["race_population"])
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_MUN", "NM_MUN"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_MUN", "NM_MUN"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_MUN", "NM_MUN"])
    table = idr.merge(rep[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_MUN", how="left", validate="one_to_one")
    table = table.merge(jovens[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_MUN", how="left", validate="one_to_one")
    table = table.merge(idosos[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_MUN", how="left", validate="one_to_one")
    st.plotly_chart(charts.horizontal_ranking(table, "Municipio", "IDR", "Municípios com Maior Diversidade Racial"), width="stretch")
    st.dataframe(
        presentation_frame(
            table,
            ["Posicao", "Municipio", "Populacao", "IDR", "Grupo racial predominante", "Representatividade feminina", "Jovens", "Idosos"],
        ),
        width="stretch",
        hide_index=True,
    )
    selected = st.selectbox("Ver bairros de um município", [""] + sorted_options(model["bairro"]["NM_MUN"]))
    if selected:
        bairros = model["bairro"][model["bairro"]["NM_MUN"].eq(selected)].sort_values("populacao_total", ascending=False)
        st.dataframe(
            presentation_frame(bairros, ["NM_BAIRRO", "NM_MUN", "populacao_total", "AREA_KM2"]),
            width="stretch",
            hide_index=True,
        )


def page_bairros(model):
    st.title("Bairros")
    idr = metrics.calcular_idr(model["race_population"], "bairro")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    table = idr.merge(rep[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    table = table.merge(jovens[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    table = table.merge(idosos[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    st.plotly_chart(charts.horizontal_ranking(table, "NM_BAIRRO", "Populacao", "Bairros Mais Populosos"), width="stretch")
    st.dataframe(
        presentation_frame(
            table,
            ["NM_BAIRRO", "NM_MUN", "Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"],
        ),
        width="stretch",
        hide_index=True,
    )


def page_demography(model):
    st.title("Demografia")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.age_pyramid(model["demo_age_sex"], "Pirâmide Etária por Sexo"), width="stretch")
    with col2:
        st.plotly_chart(charts.line_or_bar_age_by_race(model["race_age"]), width="stretch")
    age = (
        model["demo_age"]
        .groupby("Faixa_Etaria", dropna=False, observed=True)["valor"]
        .sum()
        .reset_index()
    )
    st.dataframe(presentation_frame(age), width="stretch", hide_index=True)


def page_diversity(model):
    st.title("Diversidade Racial")
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro")
    idr_mun = metrics.calcular_idr(model["race_population"], "municipio")
    col1, col2 = st.columns(2)
    with col1:
        scatter = charts.scatter_diversity_population(idr_bairro, "NM_BAIRRO")
        if scatter is None:
            st.info("Não há dados válidos de população e diversidade racial para exibir neste gráfico.")
        else:
            st.plotly_chart(scatter, width="stretch")
    with col2:
        st.plotly_chart(charts.bar_distribution(model["race_population"], "Cor_Raca", percent=True, title="Composição Racial da População"), width="stretch")
    st.subheader("Municípios com Maior Diversidade Racial", help=get_metric_help("IDR"))
    st.dataframe(
        presentation_frame(idr_mun, ["NM_MUN", "Populacao", "IDR"]),
        width="stretch",
        hide_index=True,
    )


def page_responsibles(model):
    st.title("Responsáveis pelo Domicílio")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["Cor_Raca"])
    indig = metrics.ranking_responsaveis_indigenas_40mais(model["responsible_race_age"])
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.bar_distribution(model["responsible_race_sex"], "Sexo", title="Responsáveis por Sexo"), width="stretch")
    with col2:
        st.plotly_chart(charts.bar_distribution(model["responsible_race"], "Cor_Raca", title="Responsáveis por Cor ou Raça"), width="stretch")
    st.subheader("Participação Feminina entre Responsáveis")
    st.dataframe(presentation_frame(rep), width="stretch", hide_index=True)
    st.subheader("Responsáveis Indígenas com 40 Anos ou Mais")
    st.dataframe(
        presentation_frame(indig, ["NM_BAIRRO", "NM_MUN", "Quantidade", "Total_Responsaveis", "Percentual"]),
        width="stretch",
        hide_index=True,
    )


def page_map(model):
    st.title("Mapa")
    idr = metrics.calcular_idr(model["race_population"], "bairro")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_BAIRRO"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_BAIRRO"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_BAIRRO"])
    indicator_columns = ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN", "populacao_total"]
    if "NM_UF" in model["bairro"].columns:
        indicator_columns.insert(3, "NM_UF")
    indicators = model["bairro"][indicator_columns].rename(columns={"populacao_total": "Populacao"})
    indicators = indicators.merge(idr[["CD_BAIRRO", "IDR"]], on="CD_BAIRRO", how="left", validate="one_to_one")
    indicators = indicators.merge(rep[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    indicators = indicators.merge(jovens[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    indicators = indicators.merge(idosos[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_BAIRRO", how="left", validate="one_to_one")
    indicator = st.selectbox(
        "Indicador",
        ["Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"],
        format_func=get_display_name,
        help=get_metric_help("IDR"),
    )
    map_mode = st.radio(
        "Cobertura geográfica",
        ["Brasil — pontos representativos", "Bahia — limites oficiais"],
        horizontal=True,
    )
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
    st.title("Qualidade dos Dados")
    st.subheader("Perfil das Tabelas")
    st.dataframe(presentation_frame(profile), width="stretch", hide_index=True)
    st.subheader("Tratamentos Registrados")
    st.dataframe(presentation_frame(treatment_log), width="stretch", hide_index=True)
    st.subheader("Validações")
    st.dataframe(presentation_frame(inconsistencies), width="stretch", hide_index=True)
    st.subheader("Dicionário de Dados")
    st.dataframe(
        presentation_frame(dictionary.head(300), hidden=["variavel_norm"]),
        width="stretch",
        hide_index=True,
    )


def page_exports(model, filtros):
    st.title("Exportação")
    idr_mun = metrics.ranking_municipios_diversidade(model["race_population"])
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro")
    insights = all_insights(model)
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


def page_storytelling(model):
    st.title("Análises e Narrativa")
    for insight in all_insights(model):
        st.markdown(f"<div class='note'>{insight}</div>", unsafe_allow_html=True)
        st.write("")


def page_about():
    st.title("Sobre o Projeto")
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
        page_municipios(current)
    elif page == "Bairros":
        page_bairros(current)
    elif page == "Demografia":
        page_demography(current)
    elif page == "Diversidade Racial":
        page_diversity(current)
    elif page == "Responsáveis":
        page_responsibles(current)
    elif page == "Mapa":
        page_map(current)
    elif page == "Análises e Narrativa":
        page_storytelling(current)
    elif page == "Qualidade dos Dados":
        page_quality(profile, treatment_log, inconsistencies, dictionary)
    elif page == "Exportação":
        page_exports(current, filtros)
    else:
        page_about()


if __name__ == "__main__":
    main()
