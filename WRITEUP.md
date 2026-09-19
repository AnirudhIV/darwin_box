# Write-up: AI-Powered Data Q&A App

## Approach

The brief asks for cross-file analytical Q&A over CSV/Excel data with charts,
built with open-source AI models, in 4-6 hours. The biggest risk in a task
like this is scope creep — trying to build a general-purpose "chat with your
data" agent. I scoped it down to a single, reliable path:

**Upload → register as DuckDB tables → LLM writes SQL → validate → execute →
render.** Every file/sheet becomes a DuckDB table; the LLM's only job is to
translate a question into SQL against a schema it's shown. DuckDB natively
handles joins across tables, which gets cross-file analysis "for free" instead
of building custom multi-dataframe join logic. This kept the core loop small
and let me spend the remaining time on reliability and safety rather than
plumbing.

**Stack**: DuckDB (in-memory, zero-copy over pandas), Groq running
`openai/gpt-oss-120b` (open-weight model, fast hosted inference so the demo
stays responsive). Two UIs share this same core: a polished **React +
Tailwind** frontend behind a **FastAPI** backend (primary), and a
single-file **Streamlit** app (fallback, built first to de-risk the
4-6h budget, kept working standalone). Charts render via Plotly in
Streamlit and Recharts in React, both driven by one shape-detection
heuristic in `charting.py`.

## Key decisions

- **Text-to-SQL over DuckDB, not text-to-pandas-code.** Generated SQL is far
  easier to constrain and validate than arbitrary generated Python — a
  `SELECT`-only grammar is a much smaller attack surface than `exec()`.
- **Schema-aware, compact prompting.** The model is shown table names,
  columns, DuckDB types, and 2-3 sample rows per table — enough to write
  correct joins and filters without a huge prompt. Date-like text columns are
  parsed into real timestamps at load time (not left as strings), so trend
  questions work on the first attempt instead of always needing a retry.
- **Chart selection is heuristic, not LLM-driven.** Given the result shape
  (date+numeric → line, category+numeric → bar, two numerics → scatter), a
  chart type is picked deterministically. This is faster, free, and more
  predictable than asking the model to pick chart types.

## Delta solutioning (the engineering value beyond "call an LLM")

1. **Read-only SQL validation (`sql_guard.py`)** — every generated query must
   be a single `SELECT`/`WITH` statement; a keyword blocklist scans the
   *entire* statement (not just its first token) for DDL/DML/admin keywords.
   This matters beyond generic prompt-injection hygiene: sample cell values
   from uploaded files are embedded directly in the LLM prompt, so a
   malicious CSV cell could attempt to inject SQL into the model's output.
   Scanning the whole statement text catches an injected keyword regardless
   of where it lands.
2. **Bounded self-correction.** If generation, validation, or execution
   fails, the error is fed back to the model for exactly one retry before
   surfacing a friendly failure with the raw error available on request —
   meaningfully better reliability than a single-shot call, without unbounded
   latency/cost.
3. **Transparency by default.** Every answer shows its generated SQL in an
   expander, so the user can verify what was actually run rather than
   trusting a black box — important for an analytical tool where wrong
   answers are worse than no answer.
4. **Schema-type source of truth.** Column types shown to the LLM are read
   back from DuckDB's own `DESCRIBE`, not inferred from pandas dtypes — what
   the model sees always matches what will actually execute.
5. **CSV export and per-session isolation.** Results are downloadable, and
   each visitor's `DuckDB` connection/chat history lives in its own session
   (`st.session_state` in Streamlit; an explicit `session_id` in the FastAPI
   backend) — no shared or persisted state between sessions.
6. **One core, two UIs, zero duplicated logic.** The FastAPI backend imports
   `data_manager.py`/`llm.py`/`sql_guard.py`/`charting.py` unchanged; the only
   new code is the HTTP layer and JSON serialization. The chart-selection
   heuristic itself lives in one shared function so the Plotly and Recharts
   renderers can't drift apart.

## What I'd build next

- **Multi-turn context**: let follow-up questions ("now break that down by
  month") reference the previous query/result instead of starting fresh.
- **Per-user rate limiting / API key**, since a hosted demo currently shares
  one Groq key across all visitors.
- **Dynamic schema truncation** for users uploading many files, so prompt
  size doesn't degrade answer quality past ~6 tables.
- **An LLM-assisted chart-spec fallback** for result shapes the heuristics
  don't cover, with strict validation of any column names it returns.
- **Legacy `.xls` support** and larger-file handling (currently everything is
  read fully into memory).
