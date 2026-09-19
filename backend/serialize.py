"""DataFrame -> JSON helpers. Handles the two things the stdlib/orjson
encoders choke on: NaN/NaT (not valid JSON - must become null) and
datetime64 columns (must become ISO-8601 strings)."""
import pandas as pd


def _json_safe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df.astype(object).where(pd.notnull(df), None)


def dataframe_to_table(df: pd.DataFrame) -> tuple[list[str], list[list]]:
    """Returns (columns, rows) - columnar names + row-arrays, compact for a
    table component to consume directly."""
    if df is None:
        return [], []
    safe = _json_safe(df)
    return list(safe.columns), safe.values.tolist()
