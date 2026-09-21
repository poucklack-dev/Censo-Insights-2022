from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import config

TEMPLATE = "plotly_dark"


def bar_distribution(df: pd.DataFrame, category: str, value: str = "valor", percent: bool = False, title: str = ""):
    grouped = df.groupby(category, dropna=False, observed=True)[value].sum(min_count=1).reset_index()
    y_col = value
    if percent:
        total = grouped[value].sum(min_count=1)
        grouped["Percentual"] = grouped[value] / total * 100 if total else 0
        y_col = "Percentual"
    fig = px.bar(
        grouped.sort_values(y_col, ascending=False),
        x=category,
        y=y_col,
        color=category if category == "Cor_Raca" else None,
        color_discrete_map=config.RACE_COLORS,
        template=TEMPLATE,
        title=title,
        text_auto=".2s",
    )
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=55, b=30))
    return fig


def horizontal_ranking(df: pd.DataFrame, label: str, value: str, title: str, top: int = 15):
    plot_df = df.sort_values(value, ascending=False).head(top).sort_values(value)
    fig = px.bar(plot_df, x=value, y=label, orientation="h", template=TEMPLATE, title=title, text=value)
    fig.update_traces(texttemplate="%{x:.2f}", textposition="outside")
    fig.update_layout(margin=dict(l=20, r=20, t=55, b=30), yaxis_title=None)
    return fig


def age_pyramid(demo_age_sex: pd.DataFrame, title: str = "Piramide etaria"):
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
    fig.update_layout(
        template=TEMPLATE,
        title=title,
        barmode="relative",
        bargap=0.08,
        xaxis_title="Populacao",
        yaxis_title=None,
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
        title="Faixas etarias por cor/raca",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=55, b=30), xaxis_title=None, yaxis_title="Populacao")
    return fig


def scatter_diversity_population(idr_df: pd.DataFrame, label_col: str):
    required = {"Populacao", "IDR", label_col}
    if not required.issubset(idr_df.columns):
        return None

    # Plotly does not accept NA/inf in marker.size.  Keep the modeled data
    # untouched and sanitize only the frame sent to the visualization.
    plot_df = idr_df.copy()
    plot_df["Populacao"] = pd.to_numeric(plot_df["Populacao"], errors="coerce")
    plot_df["IDR"] = pd.to_numeric(plot_df["IDR"], errors="coerce")
    plot_df[["Populacao", "IDR"]] = plot_df[["Populacao", "IDR"]].replace(
        [np.inf, -np.inf], np.nan
    )
    plot_df = plot_df.dropna(subset=["Populacao", "IDR"])
    plot_df = plot_df.loc[plot_df["Populacao"].gt(0)].copy()
    if plot_df.empty:
        return None
    plot_df["Populacao"] = plot_df["Populacao"].astype("float64")
    plot_df["IDR"] = plot_df["IDR"].astype("float64")

    fig = px.scatter(
        plot_df,
        x="Populacao",
        y="IDR",
        hover_name=label_col,
        size="Populacao",
        template=TEMPLATE,
        title="Diversidade racial x populacao",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=55, b=30))
    return fig
