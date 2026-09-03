from __future__ import annotations

import pandas as pd
import streamlit as st

from src import charts, metrics
from src.data_cleaning import clean_raw_tables, detect_inconsistencies
from src.data_loader import load_dictionary, load_raw_tables
from src.exports import csv_bytes, excel_report, pdf_insights
from src.filters import filter_frame, sorted_options
from src.insights import all_insights
from src.maps import build_choropleth
from src.modeling import build_model
from src.utils import br_number, br_percent


st.set_page_config(
    page_title="Analytics Censo 2022",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #0B1015; color: #EDF2F7; }
    [data-testid="stSidebar"] { background: #111820; border-right: 1px solid #263241; }
    .metric-card {
        border: 1px solid #263241;
        border-radius: 8px;
        padding: 16px 18px;
        background: #121A23;
        min-height: 112px;
    }
    .metric-card .label { color: #9FB0C3; font-size: .86rem; }
    .metric-card .value { color: #F7FAFC; font-size: 1.7rem; font-weight: 700; margin-top: 8px; }
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


@st.cache_data(show_spinner="Carregando e tratando dados censitarios...")
def load_project():
    raw = load_raw_tables()
    cleaned, treatment_log, profile = clean_raw_tables(raw)
    model = build_model(cleaned)
    inconsistencies = detect_inconsistencies(model)
    dictionary = load_dictionary()
    return model, treatment_log, profile, inconsistencies, dictionary


def metric_card(label: str, value: str):
    st.markdown(
        f"<div class='metric-card'><div class='label'>{label}</div><div class='value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def filtered_model(model: dict[str, pd.DataFrame], filtros: dict) -> dict[str, pd.DataFrame]:
    return {
        name: filter_frame(
            df,
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
    municipios = st.sidebar.multiselect("Municipio", sorted_options(bairro["NM_MUN"]))
    bairro_base = bairro[bairro["NM_MUN"].isin(municipios)] if municipios else bairro
    bairros = st.sidebar.multiselect("Bairro", sorted_options(bairro_base["NM_BAIRRO"]))
    sexos = st.sidebar.multiselect("Sexo", ["Masculino", "Feminino"])
    faixas = st.sidebar.multiselect(
        "Faixa etaria",
        ["0 a 14 anos", "15 a 29 anos", "30 a 39 anos", "40 a 59 anos", "60 anos ou mais"],
    )
    racas = st.sidebar.multiselect("Cor/raca", ["Branca", "Preta", "Amarela", "Parda", "Indigena"])
    page = st.sidebar.radio(
        "Pagina",
        [
            "Visao Geral",
            "Municipios",
            "Bairros",
            "Demografia",
            "Diversidade Racial",
            "Responsaveis",
            "Mapa",
            "Insights e Storytelling",
            "Qualidade dos Dados",
            "Exportacao",
            "Sobre o Projeto",
        ],
    )
    return {"municipios": municipios, "bairros": bairros, "sexos": sexos, "faixas": faixas, "racas": racas, "page": page}


def summary_kpis(model: dict[str, pd.DataFrame], filtros: dict | None = None) -> dict[str, float]:
    filtros = filtros or {}
    has_sex = bool(filtros.get("sexos"))
    has_age = bool(filtros.get("faixas"))
    has_race = bool(filtros.get("racas"))
    if has_sex and has_race and not has_age:
        pop = model["race_sex"]["valor"].sum()
    elif has_sex and has_age and not has_race:
        pop = model["demo_age_sex"]["valor"].sum()
    elif has_race or has_age:
        pop = model["race_age"]["valor"].sum()
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
    st.title("Visao Geral")
    k = summary_kpis(model, filtros)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Populacao total", br_number(k["Populacao total"]))
    with cols[1]:
        metric_card("Municipios", br_number(k["Municipios"]))
    with cols[2]:
        metric_card("Bairros", br_number(k["Bairros"]))
    with cols[3]:
        metric_card("IDR medio", br_number(k["IDR medio"], 3))
    cols = st.columns(3)
    with cols[0]:
        metric_card("Representatividade feminina", br_percent(k["Representatividade feminina"]))
    with cols[1]:
        metric_card("Proporcao de jovens", br_percent(k["Jovens"]))
    with cols[2]:
        metric_card("Proporcao de idosos", br_percent(k["Idosos"]))
    col1, col2 = st.columns([1.1, 1])
    with col1:
        mode = st.radio("Distribuicao racial", ["Quantidade", "Percentual"], horizontal=True)
        st.plotly_chart(charts.bar_distribution(model["race_population"], "Cor_Raca", percent=mode == "Percentual"), use_container_width=True)
    with col2:
        st.plotly_chart(charts.age_pyramid(model["demo_age_sex"]), use_container_width=True)


def page_municipios(model):
    st.title("Municipios")
    idr = metrics.ranking_municipios_diversidade(model["race_population"])
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_MUN", "NM_MUN"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_MUN", "NM_MUN"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_MUN", "NM_MUN"])
    table = idr.merge(rep[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_MUN", how="left")
    table = table.merge(jovens[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_MUN", how="left")
    table = table.merge(idosos[["CD_MUN", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_MUN", how="left")
    st.plotly_chart(charts.horizontal_ranking(table, "Municipio", "IDR", "Ranking de diversidade racial municipal"), use_container_width=True)
    st.dataframe(table, use_container_width=True, hide_index=True)
    selected = st.selectbox("Drill-down para bairros", [""] + sorted_options(model["bairro"]["NM_MUN"]))
    if selected:
        bairros = model["bairro"][model["bairro"]["NM_MUN"].eq(selected)].sort_values("populacao_total", ascending=False)
        st.dataframe(bairros[["NM_MUN", "NM_BAIRRO", "populacao_total", "AREA_KM2"]], use_container_width=True, hide_index=True)


def page_bairros(model):
    st.title("Bairros")
    idr = metrics.calcular_idr(model["race_population"], "bairro")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_BAIRRO", "NM_BAIRRO", "NM_MUN"])
    table = idr.merge(rep[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_BAIRRO", how="left")
    table = table.merge(jovens[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_BAIRRO", how="left")
    table = table.merge(idosos[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_BAIRRO", how="left")
    st.plotly_chart(charts.horizontal_ranking(table, "NM_BAIRRO", "Populacao", "Bairros mais populosos"), use_container_width=True)
    st.dataframe(table, use_container_width=True, hide_index=True)


def page_demography(model):
    st.title("Demografia")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.age_pyramid(model["demo_age_sex"], "Piramide etaria por sexo"), use_container_width=True)
    with col2:
        st.plotly_chart(charts.line_or_bar_age_by_race(model["race_age"]), use_container_width=True)
    age = model["demo_age"].groupby("Faixa_Etaria", dropna=False)["valor"].sum().reset_index()
    st.dataframe(age, use_container_width=True, hide_index=True)


def page_diversity(model):
    st.title("Diversidade Racial")
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro")
    idr_mun = metrics.calcular_idr(model["race_population"], "municipio")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.scatter_diversity_population(idr_bairro, "NM_BAIRRO"), use_container_width=True)
    with col2:
        st.plotly_chart(charts.bar_distribution(model["race_population"], "Cor_Raca", percent=True, title="Composicao racial"), use_container_width=True)
    st.subheader("Municipios com maior diversidade")
    st.dataframe(idr_mun, use_container_width=True, hide_index=True)


def page_responsibles(model):
    st.title("Responsaveis pelo Domicilio")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["Cor_Raca"])
    indig = metrics.ranking_responsaveis_indigenas_40mais(model["responsible_race_age"])
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.bar_distribution(model["responsible_race_sex"], "Sexo", title="Responsaveis por sexo"), use_container_width=True)
    with col2:
        st.plotly_chart(charts.bar_distribution(model["responsible_race"], "Cor_Raca", title="Responsaveis por cor/raca"), use_container_width=True)
    st.subheader("Representatividade feminina por cor/raca")
    st.dataframe(rep, use_container_width=True, hide_index=True)
    st.subheader("Responsaveis indigenas acima de 40 anos")
    st.dataframe(indig, use_container_width=True, hide_index=True)


def page_map(model):
    st.title("Mapa")
    idr = metrics.calcular_idr(model["race_population"], "bairro")
    rep = metrics.representatividade_feminina(model["responsible_race_sex"], ["CD_BAIRRO"])
    jovens = metrics.proporcao_jovens(model["demo_age"], ["CD_BAIRRO"])
    idosos = metrics.proporcao_idosos(model["demo_age"], ["CD_BAIRRO"])
    indicators = model["bairro"][["CD_BAIRRO", "NM_BAIRRO", "NM_MUN", "populacao_total"]].rename(columns={"populacao_total": "Populacao"})
    indicators = indicators.merge(idr[["CD_BAIRRO", "IDR"]], on="CD_BAIRRO", how="left")
    indicators = indicators.merge(rep[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Representatividade feminina"}), on="CD_BAIRRO", how="left")
    indicators = indicators.merge(jovens[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Jovens"}), on="CD_BAIRRO", how="left")
    indicators = indicators.merge(idosos[["CD_BAIRRO", "Percentual"]].rename(columns={"Percentual": "Idosos"}), on="CD_BAIRRO", how="left")
    indicator = st.selectbox("Indicador", ["Populacao", "IDR", "Representatividade feminina", "Jovens", "Idosos"])
    fig = build_choropleth(indicators, indicator)
    if fig is None:
        st.info("Mapa indisponivel neste ambiente. Instale geopandas e use a malha BA_bairros_CD2022 para visualizar bairros da Bahia.")
    else:
        st.plotly_chart(fig, use_container_width=True)


def page_quality(profile, treatment_log, inconsistencies, dictionary):
    st.title("Qualidade dos Dados")
    st.dataframe(profile, use_container_width=True, hide_index=True)
    st.subheader("Tratamentos registrados")
    st.dataframe(treatment_log, use_container_width=True, hide_index=True)
    st.subheader("Validacoes")
    st.dataframe(inconsistencies, use_container_width=True, hide_index=True)
    st.subheader("Dicionario")
    st.dataframe(dictionary.head(300), use_container_width=True, hide_index=True)


def page_exports(model, filtros):
    st.title("Exportacao")
    idr_mun = metrics.ranking_municipios_diversidade(model["race_population"])
    idr_bairro = metrics.calcular_idr(model["race_population"], "bairro")
    insights = all_insights(model)
    sheets = {
        "Resumo": pd.DataFrame([summary_kpis(model, filtros)]),
        "Municipios": idr_mun,
        "Bairros": idr_bairro,
        "Raca": model["race_population"],
        "Sexo": model["demo_age_sex"],
        "Faixa Etaria": model["demo_age"],
        "Responsaveis": model["responsible_race_sex"],
    }
    st.download_button("Baixar dados filtrados CSV", csv_bytes(model["bairro"]), "dados_filtrados.csv", "text/csv")
    st.download_button("Baixar relatorio Excel", excel_report(sheets), "relatorio_analytics.xlsx")
    st.download_button("Baixar insights PDF", pdf_insights("Insights Censo 2022", insights), "insights.pdf", "application/pdf")


def page_storytelling(model):
    st.title("Insights e Storytelling")
    for insight in all_insights(model):
        st.markdown(f"<div class='note'>{insight}</div>", unsafe_allow_html=True)
        st.write("")


def page_about():
    st.title("Sobre o Projeto")
    st.markdown(
        """
        Projeto analitico em Python para agregados do Censo 2022 por bairros.

        A modelagem usa `CD_BAIRRO` como chave principal, preserva os arquivos originais e cria fatos derivados para populacao por idade/sexo, populacao por cor/raca, responsaveis por sexo/cor/raca e responsaveis por faixa etaria.

        O IDR e calculado pelo indice de Simpson normalizado: `1 - soma(p_i^2)`, reescalado para o intervalo de 0 a 1 conforme o numero de categorias observadas. Como nao ha formula oficial de IDR nos arquivos fornecidos, a decisao metodologica fica explicita no codigo e na documentacao.

        A idade media de responsaveis e uma estimativa por pontos medios de faixas. Classes abertas usam ponto medio metodologico documentado, nao idade individual inventada.

        A malha geografica disponivel e da Bahia; por isso o mapa mostra somente bairros com geometria correspondente.
        """
    )


def main():
    model, treatment_log, profile, inconsistencies, dictionary = load_project()
    filtros = sidebar_filters(model)
    current = filtered_model(model, filtros)
    page = filtros["page"]
    if page == "Visao Geral":
        page_overview(current, filtros)
    elif page == "Municipios":
        page_municipios(current)
    elif page == "Bairros":
        page_bairros(current)
    elif page == "Demografia":
        page_demography(current)
    elif page == "Diversidade Racial":
        page_diversity(current)
    elif page == "Responsaveis":
        page_responsibles(current)
    elif page == "Mapa":
        page_map(current)
    elif page == "Insights e Storytelling":
        page_storytelling(current)
    elif page == "Qualidade dos Dados":
        page_quality(profile, treatment_log, inconsistencies, dictionary)
    elif page == "Exportacao":
        page_exports(current, filtros)
    else:
        page_about()


if __name__ == "__main__":
    main()
