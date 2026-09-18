"""AI-powered CSV/Excel Data Q&A app: Streamlit + DuckDB + Groq (openai/gpt-oss-120b)."""
import os

import duckdb
import streamlit as st

from charting import build_chart
from data_manager import build_schema_text, load_uploaded_file
from llm import generate_sql

st.set_page_config(page_title="Data Q&A", page_icon="\U0001F4CA", layout="wide")


def get_api_key() -> str | None:
    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")


def init_session():
    if "con" not in st.session_state:
        st.session_state.con = duckdb.connect(":memory:")
    if "tables_meta" not in st.session_state:
        st.session_state.tables_meta = {}
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def clear_session():
    st.session_state.con = duckdb.connect(":memory:")
    st.session_state.tables_meta = {}
    st.session_state.processed_files = set()
    st.session_state.chat_history = []


def handle_uploads(uploaded_files):
    for f in uploaded_files:
        key = (f.name, f.size)
        if key in st.session_state.processed_files:
            continue
        try:
            load_uploaded_file(f, st.session_state.con, st.session_state.tables_meta)
            st.session_state.processed_files.add(key)
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error(f"Failed to load {f.name}: {exc}")


def render_sidebar():
    st.sidebar.header("Data")
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV or Excel files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        handle_uploads(uploaded_files)

    if st.session_state.tables_meta:
        st.sidebar.subheader("Loaded tables")
        for name, meta in st.session_state.tables_meta.items():
            with st.sidebar.expander(f"{name} ({meta['n_rows']} rows)"):
                st.caption(f"Source: {meta['source_filename']}" + (f" / sheet '{meta['sheet']}'" if meta["sheet"] else ""))
                cols = ", ".join(c["name"] for c in meta["columns"])
                st.caption(f"Columns: {cols}")
                df_preview = st.session_state.con.execute(f'SELECT * FROM "{name}" LIMIT 5').fetchdf()
                st.dataframe(df_preview, use_container_width=True, height=150)
    else:
        st.sidebar.info("Upload at least one file to start asking questions.")

    st.sidebar.divider()
    if st.sidebar.button("Clear session", use_container_width=True):
        clear_session()
        st.rerun()


def render_turn(turn: dict):
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        if turn["error"]:
            st.error(f"I couldn't answer that: {turn['error']}")
        else:
            df = turn["result_df"]
            if df.shape == (1, 1):
                col = df.columns[0]
                st.metric(label=str(col), value=str(df.iloc[0][col]))
            else:
                st.dataframe(df, use_container_width=True)

            fig = turn.get("chart")
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

            if df is not None and not df.empty:
                st.download_button(
                    "Download result as CSV",
                    df.to_csv(index=False).encode("utf-8"),
                    file_name="result.csv",
                    mime="text/csv",
                    key=f"dl_{id(turn)}",
                )

        if turn["sql"]:
            with st.expander("View generated SQL"):
                st.code(turn["sql"], language="sql")


def main():
    init_session()
    st.title("\U0001F4CA Data Q&A")
    st.caption("Upload CSV/Excel files, then ask questions about them in plain English.")

    render_sidebar()

    api_key = get_api_key()
    if not api_key:
        st.warning(
            "No Groq API key found. Set `GROQ_API_KEY` in `.streamlit/secrets.toml` "
            "(see `.streamlit/secrets.toml.example`) or as an environment variable, then reload. "
            "See README.md for setup instructions."
        )
        return

    for turn in st.session_state.chat_history:
        render_turn(turn)

    if not st.session_state.tables_meta:
        st.info("Upload at least one CSV or Excel file in the sidebar to get started.")
        return

    question = st.chat_input("Ask a question about your data...")
    if question:
        schema_text = build_schema_text(st.session_state.tables_meta)
        with st.spinner("Thinking..."):
            outcome = generate_sql(api_key, schema_text, question, st.session_state.con)

        chart = None
        if outcome["result_df"] is not None:
            try:
                chart = build_chart(outcome["result_df"])
            except Exception:  # noqa: BLE001
                chart = None

        st.session_state.chat_history.append(
            {
                "question": question,
                "sql": outcome["sql"],
                "result_df": outcome["result_df"],
                "error": outcome["error"],
                "chart": chart,
            }
        )
        st.rerun()


if __name__ == "__main__":
    main()
