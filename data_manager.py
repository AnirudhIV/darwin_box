"""Upload -> DuckDB table registration and schema introspection."""
import re

import pandas as pd


def _sanitize(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip()).strip("_").lower()
    if not name:
        name = "col"
    if name[0].isdigit():
        name = f"c_{name}"
    return name


def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for n in names:
        if n not in seen:
            seen[n] = 1
            out.append(n)
        else:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
    return out


def _unique_table_name(base: str, existing: set[str]) -> str:
    name = base
    i = 2
    while name in existing:
        name = f"{base}_{i}"
        i += 1
    return name


def load_uploaded_file(uploaded_file, con, tables_meta: dict) -> list[str]:
    """Read one uploaded file (CSV or XLSX), register table(s) in DuckDB,
    update tables_meta, and return the list of table names created."""
    filename = uploaded_file.name
    base = _sanitize(filename.rsplit(".", 1)[0])
    created: list[str] = []

    if filename.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        table_name = _unique_table_name(base, set(tables_meta.keys()))
        _register_table(con, tables_meta, table_name, df, filename, sheet=None)
        created.append(table_name)

    elif filename.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        multi_sheet = len(xls.sheet_names) > 1
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            table_base = _sanitize(f"{base}_{sheet}") if multi_sheet else base
            table_name = _unique_table_name(table_base, set(tables_meta.keys()))
            _register_table(con, tables_meta, table_name, df, filename, sheet=sheet)
            created.append(table_name)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    return created


_DATE_NAME_RE = re.compile(r"(date|time|_dt$|_at$|^dt_)", re.IGNORECASE)


def _coerce_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parses columns that look like dates (by name, and >=90% parseable) so
    DuckDB sees a real DATE/TIMESTAMP type instead of VARCHAR - otherwise
    every trend/date_trunc question fails until the self-correction retry
    adds an explicit CAST."""
    for col in df.columns:
        is_textlike = pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])
        if not is_textlike or not _DATE_NAME_RE.search(str(col)):
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null > 0 and parsed.notna().sum() / non_null >= 0.9:
            df[col] = parsed
    return df


def _register_table(con, tables_meta: dict, table_name: str, df: pd.DataFrame, filename: str, sheet):
    original_columns = list(df.columns)
    sanitized_columns = _dedupe([_sanitize(c) for c in original_columns])
    df = df.copy()
    df.columns = sanitized_columns
    df = _coerce_date_columns(df)

    con.register(table_name, df)

    described = con.execute(f'DESCRIBE "{table_name}"').fetchall()
    columns = [{"name": row[0], "type": row[1]} for row in described]

    sample_rows = df.head(3).to_dict(orient="records")
    sample_rows = [
        {k: (str(v)[:40] if v is not None else None) for k, v in row.items()}
        for row in sample_rows
    ]

    tables_meta[table_name] = {
        "source_filename": filename,
        "sheet": sheet,
        "n_rows": len(df),
        "columns": columns,
        "column_mapping": dict(zip(sanitized_columns, original_columns)),
        "sample_rows": sample_rows,
    }


def build_schema_text(tables_meta: dict) -> str:
    """Compact schema description sent to the LLM."""
    if not tables_meta:
        return "(no tables loaded)"

    blocks = []
    for table_name, meta in tables_meta.items():
        cols = ", ".join(f"{c['name']} ({c['type']})" for c in meta["columns"])
        block = [
            f"Table: {table_name} (from {meta['source_filename']}, {meta['n_rows']} rows)",
            f"Columns: {cols}",
        ]
        if meta["sample_rows"]:
            headers = list(meta["sample_rows"][0].keys())
            block.append("Sample rows:")
            block.append(" | ".join(headers))
            for row in meta["sample_rows"]:
                block.append(" | ".join(str(row.get(h, "")) for h in headers))
        blocks.append("\n".join(block))

    return "\n\n".join(blocks)
