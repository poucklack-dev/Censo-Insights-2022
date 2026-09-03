from __future__ import annotations

from io import BytesIO

import pandas as pd

from .utils import dataframe_to_csv, dataframe_to_excel


def csv_bytes(df: pd.DataFrame) -> bytes:
    return dataframe_to_csv(df)


def excel_report(sheets: dict[str, pd.DataFrame]) -> bytes:
    return dataframe_to_excel(sheets)


def pdf_insights(title: str, insights: list[str]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 14)]
    for insight in insights:
        story.append(Paragraph(insight, styles["BodyText"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return output.getvalue()

