# Data Q&A

Upload one or more CSV/Excel files and ask analytical questions about them in
plain English. The app turns your question into SQL, runs it against your
data, and shows a table, a chart (when one makes sense), and the generated
SQL for transparency.

There are **two ways to run this app**, sharing the same core logic:

- **React + FastAPI** (`frontend/` + `backend/`) — the primary, polished UI.
- **Streamlit** (`app.py`) — a single-file fallback, kept working standalone.

## Tech stack

- **DuckDB** (in-memory) — every uploaded file/sheet becomes a DuckDB table;
  DuckDB executes the generated SQL, including joins across files/sheets.
- **Groq API running `openai/gpt-oss-120b`** — an open-weight model (Apache
  2.0 licensed; Groq just hosts fast inference) used for text-to-SQL
  generation.
- **Chart selection**: a shared heuristic (`charting.py`) picks a chart type
  from the query result's shape — no extra LLM call needed. Rendered with
  **Plotly** in Streamlit and **Recharts** in React.
- **pandas / openpyxl** — reading CSV and `.xlsx` files.
- **React frontend**: Vite + TypeScript + Tailwind CSS.
- **Backend API**: FastAPI, wrapping the same `data_manager.py` / `llm.py` /
  `sql_guard.py` modules the Streamlit app uses — no logic duplicated.

See [WRITEUP.md](WRITEUP.md) for the approach, key decisions, and what's next.

## How it works

1. You upload CSV/XLSX files. Each CSV becomes one DuckDB table; each sheet
   of an XLSX file becomes its own table. Column/table names are sanitized
   to snake_case, and date-like text columns are parsed into real timestamps
   so date functions work.
2. You ask a question. The app builds a compact text description of every
   table's schema (columns, types, a few sample rows) and asks the LLM to
   write a single read-only SQL query answering the question.
3. The generated SQL is validated (`sql_guard.py`) — only a single
   `SELECT`/`WITH` statement, no DDL/DML/admin keywords anywhere in it — then
   executed against DuckDB. If generation, validation, or execution fails,
   the error is fed back to the model for **one** self-correction retry
   before giving up gracefully.
4. The result renders as a table (or a single metric for a scalar answer),
   plus a chart if the shape of the result suggests one (a trend → line
   chart, a category breakdown → bar chart, two numeric columns → scatter).
   The generated SQL is always available for inspection, and results can be
   downloaded as CSV.

## Groq API key (needed for both run paths)

Get a free key at [console.groq.com](https://console.groq.com) (API Keys
section). You'll set it in one of these places depending on which app you run:

- Streamlit: `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.example`)
- FastAPI backend: `backend/.env` (copy from `backend/.env.example`)

Both are gitignored — never commit real keys.

## Option A: React + FastAPI (primary)

Requires Python 3.11–3.13 and Node 18+.

**Backend:**
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

# copy backend/.env.example to backend/.env and set GROQ_API_KEY

uvicorn backend.main:app --reload --port 8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). The frontend
talks to the backend at `http://localhost:8000` by default (override via
`frontend/.env`, copied from `frontend/.env.example`).

### Deploying

- **Backend → Render**: connect the repo, Render will pick up
  `backend/render.yaml` (root dir `backend`, start command
  `uvicorn main:app --host 0.0.0.0 --port $PORT`). Set `GROQ_API_KEY` and
  `FRONTEND_ORIGIN` (your Vercel URL) as secrets in the Render dashboard.
- **Frontend → Vercel**: import the repo, set the project root to `frontend/`,
  and set `VITE_API_BASE_URL` to your Render backend URL as an environment
  variable.

## Option B: Streamlit (fallback)

Requires Python 3.11–3.13 (developed/tested on 3.13; `duckdb`/`pandas` wheels
may lag behind very new Python releases).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and set GROQ_API_KEY

streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

### Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at this repo/branch, main file `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your-key-here"
   ```
4. Deploy. The app will use `runtime.txt` (Python 3.13) automatically.

## Try it

Upload the sample files in `sample_data/` (or your own) and ask:

- "What's the total order amount by region?"
- "Show me the monthly order trend."
- "Which customers have cancelled orders?"

## Limitations

- No auth or per-user isolation on a hosted deployment — every visitor shares
  the same Groq API key/quota.
- Nothing is persisted to disk. Streamlit keeps state in `st.session_state`
  per browser tab; the FastAPI backend keeps an in-memory `{session_id: ...}`
  dict with no eviction — either way, a server restart loses all sessions,
  and the React app treats an unrecognized `session_id` as "please re-upload."
- Schema prompts aren't dynamically truncated — uploading many files (roughly
  6+) may degrade answer quality since the whole schema is sent every turn.
- Legacy `.xls` Excel files aren't supported, only `.xlsx`.
