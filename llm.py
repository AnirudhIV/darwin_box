"""Groq-backed text-to-SQL generation with a bounded self-correction retry."""
import re

from groq import Groq

from sql_guard import validate_sql

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a SQL generation assistant. You write DuckDB-compatible SQL to answer
questions about the user's uploaded data.

Rules:
1. Output ONLY one SQL query, wrapped in a ```sql fenced code block. No prose
   before or after.
2. Only a SELECT or WITH...SELECT statement is allowed. Never write INSERT,
   UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH, DETACH, COPY, PRAGMA, EXPORT,
   IMPORT, INSTALL, LOAD, or any other DDL/DML/admin statement.
3. Only reference tables and columns from the schema below. Never invent
   table or column names.
4. For questions spanning multiple tables, JOIN on matching key columns
   inferred from column names (e.g. customer_id appearing in both tables).
5. Use DuckDB SQL syntax (e.g. date_trunc, strftime, list/struct functions).
6. If the question cannot be answered with the given schema, output:
   SELECT 'No matching data found for this question.' AS message;
7. Alias aggregate expressions with clear names, e.g. SUM(amount) AS total_amount.
8. Do not use LIMIT unless the question implies "top N"; otherwise cap at 500
   rows with LIMIT 500 for non-aggregate results.
"""

_SQL_FENCE_RE = re.compile(r"```sql\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_ANY_FENCE_RE = re.compile(r"```\s*(.*?)```", re.DOTALL)
_SELECT_ONWARD_RE = re.compile(r"\b(SELECT|WITH)\b.*", re.DOTALL | re.IGNORECASE)


class SqlExtractionError(Exception):
    pass


def extract_sql(text: str) -> str:
    match = _SQL_FENCE_RE.search(text)
    if match:
        return match.group(1).strip().rstrip(";").strip()

    match = _ANY_FENCE_RE.search(text)
    if match:
        return match.group(1).strip().rstrip(";").strip()

    match = _SELECT_ONWARD_RE.search(text)
    if match:
        return match.group(0).strip().rstrip(";").strip()

    raise SqlExtractionError("Could not find a SQL query in the model's response.")


def _get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def _call_model(client: Groq, messages: list[dict]) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )
    return completion.choices[0].message.content


def generate_sql(api_key: str, schema_text: str, question: str, con) -> dict:
    """Runs the generate -> extract -> validate -> execute pipeline with a
    single self-correction retry on any failure. Returns a dict with keys:
    sql, result_df (or None), error (or None), attempts.
    """
    client = _get_client(api_key)
    user_prompt = f"{schema_text}\n\nQuestion: {question}\n\nWrite the SQL query."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    attempt_sql = None
    last_error = None

    for attempt in range(2):  # first attempt + 1 retry
        raw = _call_model(client, messages)
        try:
            attempt_sql = extract_sql(raw)
            ok, reason = validate_sql(attempt_sql)
            if not ok:
                raise ValueError(reason)
            result_df = con.execute(attempt_sql).fetchdf()
            return {"sql": attempt_sql, "result_df": result_df, "error": None, "attempts": attempt + 1}
        except Exception as exc:  # noqa: BLE001 - feed any failure back for self-correction
            last_error = str(exc)
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous query failed.\nQuery: {attempt_sql}\nError: {last_error}\n"
                        "Fix the query, following all the same rules. Output only the corrected SQL."
                    ),
                }
            )

    return {"sql": attempt_sql, "result_df": None, "error": last_error, "attempts": 2}
