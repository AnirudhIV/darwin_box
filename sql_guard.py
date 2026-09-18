"""Read-only SQL validation. Rejects anything but a single SELECT/WITH query.

This is the primary safety control: the LLM prompt embeds sample cell values
from user-uploaded files, so a malicious CSV cell could attempt a prompt
injection designed to make the model emit destructive SQL. The keyword scan
below runs over the *entire* statement text (not just the first token) so it
still catches an injected keyword wherever it lands.
"""
import re

_BLOCKLIST = [
    "DROP", "ALTER", "DELETE", "INSERT", "UPDATE", "CREATE", "ATTACH", "DETACH",
    "COPY", "PRAGMA", "EXPORT", "IMPORT", "CALL", "INSTALL", "LOAD", "SET",
    "RESET", "VACUUM", "CHECKPOINT", "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION",
]
_BLOCKLIST_RE = re.compile(r"\b(" + "|".join(_BLOCKLIST) + r")\b", re.IGNORECASE)

_LINE_COMMENT_RE = re.compile(r"--[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(sql: str) -> str:
    sql = _BLOCK_COMMENT_RE.sub(" ", sql)
    sql = _LINE_COMMENT_RE.sub(" ", sql)
    return sql


def validate_sql(sql: str) -> tuple[bool, str | None]:
    """Returns (is_valid, reason_if_invalid)."""
    if not sql or not sql.strip():
        return False, "Empty query."

    stripped = _strip_comments(sql).strip()

    statements = [s.strip() for s in stripped.split(";") if s.strip()]
    if len(statements) != 1:
        return False, "Only a single SQL statement is allowed."

    statement = statements[0]

    if not re.match(r"^\s*(SELECT|WITH)\b", statement, re.IGNORECASE):
        return False, "Only SELECT/WITH...SELECT statements are allowed."

    match = _BLOCKLIST_RE.search(statement)
    if match:
        return False, f"Disallowed keyword found: {match.group(1).upper()}"

    return True, None
