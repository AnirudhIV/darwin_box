"""FastAPI API wrapping the existing DuckDB/Groq text-to-SQL logic for the
React frontend. Imports data_manager/llm/sql_guard/charting from the repo
root unchanged - this file is the only new integration surface."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from charting import select_chart_spec
from data_manager import build_schema_text, load_uploaded_file
from llm import generate_sql
from sessions import create_session, get_session
from serialize import dataframe_to_table

load_dotenv()

app = FastAPI(default_response_class=ORJSONResponse)

_frontend_origin = os.environ.get("FRONTEND_ORIGIN", "")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in ["http://localhost:5173", _frontend_origin] if o],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class _FileAdapter:
    """Adapts FastAPI's UploadFile to the .name + file-object interface
    data_manager.load_uploaded_file expects (matches Streamlit's UploadedFile).
    Excel parsing (openpyxl/zipfile) needs more than read()/seek() - tell(),
    seekable(), etc. - so unknown attributes delegate straight to the
    underlying SpooledTemporaryFile rather than re-declaring each one."""

    def __init__(self, upload: UploadFile):
        self.name = upload.filename
        self._file = upload.file

    def __getattr__(self, name):
        return getattr(self._file, name)


def _table_summaries(tables_meta: dict) -> list[dict]:
    return [
        {
            "name": name,
            "source_filename": meta["source_filename"],
            "sheet": meta["sheet"],
            "n_rows": meta["n_rows"],
            "columns": meta["columns"],
        }
        for name, meta in tables_meta.items()
    ]


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_key_configured": bool(os.environ.get("GROQ_API_KEY"))}


@app.post("/api/upload")
async def upload(files: list[UploadFile], session_id: str | None = Form(None)):
    if not files:
        raise HTTPException(400, "No files provided.")

    session = get_session(session_id) if session_id else None
    if session is None:
        session_id = create_session()
        session = get_session(session_id)

    errors = []
    for f in files:
        try:
            load_uploaded_file(_FileAdapter(f), session["con"], session["tables_meta"])
        except Exception as exc:  # noqa: BLE001
            errors.append({"filename": f.filename, "error": str(exc)})

    return {
        "session_id": session_id,
        "tables": _table_summaries(session["tables_meta"]),
        "errors": errors,
    }


@app.get("/api/tables")
def tables(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(404, "Unknown session_id")

    con = session["con"]
    summaries = _table_summaries(session["tables_meta"])
    for summary in summaries:
        preview_df = con.execute(f'SELECT * FROM "{summary["name"]}" LIMIT 5').fetchdf()
        columns, rows = dataframe_to_table(preview_df)
        summary["preview"] = {"columns": columns, "rows": rows}

    return {"tables": summaries}


@app.post("/api/ask")
def ask(body: dict):
    session_id = body.get("session_id")
    question = body.get("question")
    if not question:
        raise HTTPException(400, "Missing question.")

    session = get_session(session_id) if session_id else None
    if session is None:
        raise HTTPException(404, "Unknown session_id")
    if not session["tables_meta"]:
        raise HTTPException(400, "No tables loaded for this session.")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY is not configured on the server.")

    schema_text = build_schema_text(session["tables_meta"])
    outcome = generate_sql(api_key, schema_text, question, session["con"])

    result_df = outcome["result_df"]
    columns, rows = dataframe_to_table(result_df)
    is_scalar = len(columns) == 1 and len(rows) == 1

    chart = None
    if result_df is not None:
        try:
            chart = select_chart_spec(result_df)
        except Exception:  # noqa: BLE001
            chart = None

    return {
        "sql": outcome["sql"],
        "columns": columns,
        "rows": rows,
        "is_scalar": is_scalar,
        "chart": chart,
        "error": outcome["error"],
        "attempts": outcome["attempts"],
    }
