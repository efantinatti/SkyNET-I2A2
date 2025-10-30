import pandas as pd
import numpy as np
from typing import Dict, Any, List
import plotly.express as px


def describe_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    desc = df.describe(include='all').to_dict()
    return desc


def detect_outliers_iqr(series: pd.Series) -> List[int]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return series[(series < lower) | (series > upper)].index.tolist()


def build_charts(df: pd.DataFrame, value_col: str = 'total', date_col: str = 'data_emissao', group_col: str = 'tipo') -> List[Dict[str, Any]]:
    charts = []
    if value_col in df.columns:
        fig = px.histogram(df, x=value_col, nbins=40, title='Distribuição de valores')
        charts.append({'type': 'histogram', 'figure': fig.to_dict()})

        fig2 = px.box(df, y=value_col, title='Boxplot de valores')
        charts.append({'type': 'boxplot', 'figure': fig2.to_dict()})

    if group_col in df.columns:
        fig3 = px.pie(df, names=group_col, title='Composição por tipo')
        charts.append({'type': 'pie', 'figure': fig3.to_dict()})

    if date_col in df.columns:
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            ts = df.groupby(pd.Grouper(key=date_col, freq='D'))[value_col].sum().reset_index()
            fig4 = px.line(ts, x=date_col, y=value_col, title='Série temporal')
            charts.append({'type': 'timeseries', 'figure': fig4.to_dict()})
        except Exception:
            pass

    return charts
