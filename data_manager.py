"""Upload -> DuckDB table registration and schema introspection."""
import csv
import io
import re
import warnings

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


_HEADER_SCAN_ROWS = 30


def _promote_header(raw: pd.DataFrame) -> pd.DataFrame:
    """Real-world sheets often have title/merged banner rows above the actual
    header (and empty leading columns). pandas would treat the first banner row
    as the header, yielding 'Unnamed: N' columns. Instead, drop fully-empty
    rows/cols, find the first row that is 'wide' (title rows have 1 filled
    cell, the header row has ~as many as the data) and mostly text, and use it
    as the header."""
    raw = raw.dropna(how="all").dropna(axis=1, how="all")
    if raw.empty:
        return raw

    scan = raw.head(_HEADER_SCAN_ROWS)
    counts = scan.notna().sum(axis=1)
    threshold = max(2, -(-counts.max() * 6 // 10)) if counts.max() > 1 else 1

    header_pos = 0
    for pos in range(len(scan)):
        row = scan.iloc[pos]
        filled = row.dropna()
        if len(filled) < threshold:
            continue
        text_cells = sum(not isinstance(v, (int, float, bool)) for v in filled)
        if text_cells / len(filled) >= 0.6:
            header_pos = pos
            break

    header = raw.iloc[header_pos]
    df = raw.iloc[header_pos + 1:].copy()
    df.columns = [
        " ".join(str(v).split()) if pd.notna(v) and str(v).strip() else f"col_{i}"
        for i, v in enumerate(header)
    ]
    return df.reset_index(drop=True).infer_objects()


def _unique_name(base: str, taken) -> str:
    name, i = base, 2
    while name in taken:
        name, i = f"{base}_{i}", i + 1
    return name


def _unpivot_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attendance/roster style grids have one column per date (Employee | Dept |
    2024-01-01 | 2024-01-02 ...). That is painful to query, so when most columns
    are dates, melt them into long form: the other columns are kept as ids, plus
    a real `date` column and a `value` column. Left alone unless >=5 columns and
    >=half of all columns have date-like headers."""
    df = df.copy()
    df.columns = _dedupe([str(c) for c in df.columns])

    date_cols: dict[str, pd.Timestamp] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for col in df.columns:
            text = col.strip()
            if len(text) < 5 or text.isdigit():
                continue
            ts = pd.to_datetime(text, errors="coerce")
            if pd.notna(ts):
                date_cols[col] = ts

    if len(date_cols) < 5 or len(date_cols) < len(df.columns) / 2:
        return df

    id_cols = [c for c in df.columns if c not in date_cols]
    date_name = _unique_name("date", id_cols)
    value_name = _unique_name("value", id_cols + [date_name])
    long = df.melt(id_vars=id_cols, value_vars=list(date_cols), var_name=date_name, value_name=value_name)
    long[date_name] = long[date_name].map(date_cols)
    long = long.dropna(subset=[value_name]).reset_index(drop=True)

    values = long[value_name]
    if values.map(type).nunique() > 1:  # e.g. numbers mixed with 'A'/'P' codes
        long[value_name] = values.astype(str)
    return long.infer_objects()


def _read_csv_ragged(uploaded_file) -> pd.DataFrame:
    """Reads a CSV whose rows may have differing field counts (report exports
    with a short title block above a wide table). pd.read_csv infers the width
    from the first lines and raises 'Expected 2 fields, saw 70'; here every row
    is padded to the widest one, then header detection runs as for Excel."""
    data = uploaded_file.read()
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            data = data.decode("latin-1")
    rows = list(csv.reader(io.StringIO(data)))
    width = max((len(r) for r in rows), default=0)
    raw = pd.DataFrame(
        [[(c.strip() or None) for c in r] + [None] * (width - len(r)) for r in rows]
    )
    df = _promote_header(raw)
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() == df[col].notna().sum():
                df[col] = converted
    return _unpivot_date_columns(df)


def load_uploaded_file(uploaded_file, con, tables_meta: dict) -> list[str]:
    """Read one uploaded file (CSV or XLSX), register table(s) in DuckDB,
    update tables_meta, and return the list of table names created."""
    filename = uploaded_file.name
    base = _sanitize(filename.rsplit(".", 1)[0])
    created: list[str] = []

    if filename.lower().endswith(".csv"):
        df = _read_csv_ragged(uploaded_file)
        table_name = _unique_table_name(base, set(tables_meta.keys()))
        _register_table(con, tables_meta, table_name, df, filename, sheet=None)
        created.append(table_name)

    elif filename.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        multi_sheet = len(xls.sheet_names) > 1
        for sheet in xls.sheet_names:
            df = _unpivot_date_columns(_promote_header(pd.read_excel(xls, sheet_name=sheet, header=None)))
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


def remove_table(table_name: str, con, tables_meta: dict) -> bool:
    """Unregisters one table/sheet from the session. Returns False if the
    table wasn't loaded (no-op), True if it was removed."""
    if table_name not in tables_meta:
        return False
    con.unregister(table_name)
    del tables_meta[table_name]
    return True
