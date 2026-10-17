from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import config
from .presentation import DISPLAY_NAMES
from .utils import br_number, br_percent

TEMPLATE = "plotly_dark"


def bar_distribution(df: pd.DataFrame, category: str, value: str = "valor", percent: bool = False, title: str = ""):
    grouped = df.groupby(category, dropna=False, observed=True)[value].sum(min_count=1).reset_index()
    y_col = value
    if percent:
        total = grouped[value].sum(min_count=1)
        grouped["Percentual"] = grouped[value] / total * 100 if total else 0
        y_col = "Percentual"
    grouped["Rótulo"] = grouped[y_col].map(
        lambda amount: br_percent(amount) if percent else br_number(amount)
    )
    fig = px.bar(
        grouped.sort_values(y_col, ascending=False),
        x=category,
        y=y_col,
        text="Rótulo",
        color=category if category == "Cor_Raca" else None,
        color_discrete_map=config.RACE_COLORS,
        template=TEMPLATE,
        title=title,
        labels=DISPLAY_NAMES,
    )
    hover_label = "Participação" if percent else "Quantidade"
    fig.update_traces(
        texttemplate="%{text}",
        hovertemplate=f"%{{x}}<br>{hover_label}: %{{text}}<extra></extra>",
    )
    fig.update_layout(
        showlegend=False,
        separators=",.",
        margin=dict(l=20, r=20, t=55, b=30),
    )
    fig.update_yaxes(
        tickformat=",.1f" if percent else ",.0f",
        ticksuffix="%" if percent else "",
    )
    return fig


def horizontal_ranking(df: pd.DataFrame, label: str, value: str, title: str, top: int = 15):
    plot_df = df.sort_values(value, ascending=False).head(top).sort_values(value)
    normalized_value = value.casefold()
    is_percent = (
        "%" in value
        or "percentual" in normalized_value
        or "representatividade" in normalized_value
        or normalized_value in {"jovens", "idosos"}
    )
    decimals = (
        1
        if is_percent
        or any(term in normalized_value for term in ("densidade", "area", "média", "media"))
        else 2
        if "idr" in normalized_value or "diversidade" in normalized_value
        else 0
    )
    plot_df["Rótulo"] = plot_df[value].map(
        lambda amount: br_percent(amount, decimals)
        if is_percent
        else br_number(amount, decimals)
    )
    fig = px.bar(
        plot_df,
        x=value,
        y=label,
        orientation="h",
        template=TEMPLATE,
        title=title,
        text="Rótulo",
        labels=DISPLAY_NAMES,
    )
    fig.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        hovertemplate=f"%{{y}}<br>{DISPLAY_NAMES.get(value, value)}: %{{text}}<extra></extra>",
    )
    fig.update_layout(
        separators=",.",
        margin=dict(l=20, r=20, t=55, b=30),
        yaxis_title=None,
    )
    fig.update_xaxes(
        tickformat=",.1f" if is_percent or decimals == 1 else ",.2f" if decimals == 2 else ",.0f",
        ticksuffix="%" if is_percent else "",
    )
    return fig


def age_pyramid(demo_age_sex: pd.DataFrame, title: str = "Pirâmide Etária"):
    grouped = (
        demo_age_sex.groupby(["Faixa_Etaria_Original", "Sexo"], dropna=False, observed=True)["valor"]
        .sum(min_count=1)
        .reset_index()
    )
    order = list(config.DEMO_AGE_COLS.keys())
    male = grouped[grouped["Sexo"].eq("Masculino")].set_index("Faixa_Etaria_Original")["valor"].reindex(order)
    female = grouped[grouped["Sexo"].eq("Feminino")].set_index("Faixa_Etaria_Original")["valor"].reindex(order)
    fig = go.Figure()
    fig.add_bar(y=order, x=-male, orientation="h", name="Masculino", marker_color="#4C78A8")
    fig.add_bar(y=order, x=female, orientation="h", name="Feminino", marker_color="#F58518")
    fig.update_traces(
        customdata=[
            [br_number(abs(value)) for value in trace.x]
            for trace in fig.data
        ],
        hovertemplate="%{y}<br>%{fullData.name}: %{customdata}<extra></extra>",
    )
    fig.update_layout(
        template=TEMPLATE,
        title=title,
        barmode="relative",
        bargap=0.08,
        xaxis_title="População",
        yaxis_title=None,
        separators=",.",
        xaxis_tickformat=",.0f",
        margin=dict(l=20, r=20, t=55, b=30),
    )
    return fig


def line_or_bar_age_by_race(race_age: pd.DataFrame):
    grouped = race_age.groupby(["Faixa_Etaria", "Cor_Raca"], dropna=False, observed=True)["valor"].sum(min_count=1).reset_index()
    fig = px.bar(
        grouped,
        x="Faixa_Etaria",
        y="valor",
        color="Cor_Raca",
        barmode="group",
        color_discrete_map=config.RACE_COLORS,
        template=TEMPLATE,
        title="População por Faixa Etária e Cor ou Raça",
        labels=DISPLAY_NAMES,
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis_title=None,
        yaxis_title="População",
        separators=",.",
    )
    fig.update_yaxes(tickformat=",.0f")
    fig.update_traces(
        hovertemplate="%{x}<br>Cor ou raça: %{fullData.name}<br>População: %{y:,.0f}<extra></extra>"
    )
    return fig


def population_diversity_by_band(idr_df: pd.DataFrame):
    required = {"Populacao", "IDR"}
    if not required.issubset(idr_df.columns):
        return None

    plot_df = idr_df[["Populacao", "IDR"]].copy()
    plot_df["Populacao"] = pd.to_numeric(plot_df["Populacao"], errors="coerce")
    plot_df["IDR"] = pd.to_numeric(plot_df["IDR"], errors="coerce")
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna()
    plot_df = plot_df.loc[
        plot_df["Populacao"].gt(0) & plot_df["IDR"].between(0, 1)
    ].copy()
    if plot_df.empty:
        return None

    bands = ["Até 1.000", "1.001–5.000", "5.001–20.000", "Acima de 20.000"]
    plot_df["Faixa populacional"] = pd.cut(
        plot_df["Populacao"],
        bins=[0, 1_000, 5_000, 20_000, np.inf],
        labels=bands,
        include_lowest=True,
    )
    summary = (
        plot_df.groupby("Faixa populacional", observed=True)
        .agg(IDR_medio=("IDR", "mean"), Bairros=("IDR", "size"))
        .reindex(bands)
        .dropna(subset=["IDR_medio"])
        .reset_index()
    )
    if summary.empty:
        return None

    summary["Rótulo"] = summary.apply(
        lambda row: (
            f"IDR {br_number(row['IDR_medio'], 2)}"
            f"<br>{br_number(row['Bairros'])} bairros"
        ),
        axis=1,
    )
    customdata = np.column_stack(
        [
            summary["Bairros"].map(br_number),
            summary["IDR_medio"].map(lambda value: br_number(value, 2)),
        ]
    )
    fig = go.Figure(
        go.Bar(
            x=summary["Faixa populacional"].astype(str),
            y=summary["IDR_medio"],
            text=summary["Rótulo"],
            customdata=customdata,
            marker_color="#64899B",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{x} habitantes<br>IDR médio: %{customdata[1]}"
                "<br>Bairros: %{customdata[0]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMPLATE,
        title="IDR Médio por Faixa de População do Bairro",
        xaxis_title="População do bairro",
        yaxis={
            "title": "IDR médio",
            "range": [0, 1],
            "tickvals": np.arange(0, 1.01, 0.2),
            "ticktext": [br_number(value, 1) for value in np.arange(0, 1.01, 0.2)],
        },
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=45),
    )
    return fig
