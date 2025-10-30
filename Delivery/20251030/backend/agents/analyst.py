from ..tools import eda_analyzer
import pandas as pd
from typing import Dict, Any, List


def analyze_csv(path: str, value_col: str = 'total', date_col: str = 'data_emissao', group_col: str = 'tipo') -> Dict[str, Any]:
    df = pd.read_csv(path)
    stats = eda_analyzer.describe_dataframe(df)
    charts = eda_analyzer.build_charts(df, value_col=value_col, date_col=date_col, group_col=group_col)
    outliers = []
    if value_col in df.columns:
        outliers = eda_analyzer.detect_outliers_iqr(df[value_col])
    return {
        'stats': stats,
        'charts': charts,
        'outliers': outliers
    }
