# Data Q&A

Upload one or more CSV/Excel files and ask analytical questions about them in
plain English. The app turns your question into SQL, runs it against your
data, and shows a table, a chart (when one makes sense), and the generated
SQL for transparency.

## Tech stack

- **Streamlit** — single-page app (upload UI, chat interface, results).
- **DuckDB** (in-memory) — every uploaded file/sheet becomes a DuckDB table;
  DuckDB executes the generated SQL, including joins across files/sheets.
- **Groq API running `openai/gpt-oss-120b`** — an open-weight model (Apache
  2.0 licensed; Groq just hosts fast inference) used for text-to-SQL
  generation.
- **Plotly** — chart rendering, chart type picked by simple heuristics on the
  query result shape (no LLM call needed for this part).
- **pandas / openpyxl** — reading CSV and `.xlsx` files.

See [WRITEUP.md](WRITEUP.md) for the approach, key decisions, and what's next.

## How it works

1. You upload CSV/XLSX files in the sidebar. Each CSV becomes one DuckDB
   table; each sheet of an XLSX file becomes its own table. Column/table
   names are sanitized to snake_case, and date-like text columns are parsed
   into real timestamps so date functions work.
2. You ask a question in the chat box. The app builds a compact text
   description of every table's schema (columns, types, a few sample rows)
   and asks the LLM to write a single read-only SQL query answering the
   question.
3. The generated SQL is validated (`sql_guard.py`) — only a single
   `SELECT`/`WITH` statement, no DDL/DML/admin keywords anywhere in it — then
   executed against DuckDB. If generation, validation, or execution fails,
   the error is fed back to the model for **one** self-correction retry
   before giving up gracefully.
4. The result renders as a table (or a single metric for a scalar answer),
   plus a chart if the shape of the result suggests one (a trend → line
   chart, a category breakdown → bar chart, two numeric columns → scatter).
   The generated SQL is always available in an expander, and results can be
   downloaded as CSV.

## Local setup

Requires Python 3.11–3.13 (developed/tested on 3.13; `duckdb`/`pandas` wheels
may lag behind very new Python releases).

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Groq API key

Get a free key at [console.groq.com](https://console.groq.com) (API Keys
section), then either:

- Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and
  paste your key in, **or**
- Set an environment variable: `GROQ_API_KEY=your-key-here`

`.streamlit/secrets.toml` is gitignored — never commit real keys.

### Run

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`), upload the
sample files in `sample_data/` (or your own), and start asking questions.
Try:

- "What's the total order amount by region?"
- "Show me the monthly order trend."
- "Which customers have cancelled orders?"

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at this repo/branch, main file `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your-key-here"
   ```
4. Deploy. The app will use `runtime.txt` (Python 3.13) automatically.

## Limitations

- No auth or per-user isolation on a hosted deployment — every visitor shares
  the same Groq API key/quota.
- Nothing is persisted to disk; uploaded data and chat history live only in
  the browser session's memory and are lost on refresh/restart.
- Schema prompts aren't dynamically truncated — uploading many files (roughly
  6+) may degrade answer quality since the whole schema is sent every turn.
- Legacy `.xls` Excel files aren't supported, only `.xlsx`.
