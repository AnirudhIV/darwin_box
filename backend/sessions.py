"""In-memory per-session state: one DuckDB connection + table metadata per
session_id. No persistence, no eviction - same ephemeral design as the
Streamlit app's st.session_state, just keyed explicitly since FastAPI has no
per-browser-tab session concept of its own. A backend restart loses all
sessions; the frontend treats a 404 on an unknown session_id as "please
re-upload"."""
import uuid

import duckdb

SESSIONS: dict[str, dict] = {}


def create_session() -> str:
    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = {"con": duckdb.connect(":memory:"), "tables_meta": {}}
    return session_id


def get_session(session_id: str) -> dict | None:
    return SESSIONS.get(session_id)
