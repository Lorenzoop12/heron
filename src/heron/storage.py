"""Store the triage verdicts in a SQLite database."""

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from heron.models import TriageResult

_SCHEMA = """
CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score INTEGER NOT NULL,
    findings TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class VerdictRepository(Protocol):
    """The port: what the application needs from a verdict store."""

    def save(self, results: Iterable[TriageResult]) -> int: ...

    def count(self, verdict: str | None = None) -> int: ...


class VerdictStore:
    """The SQLite adapter for :class:`VerdictRepository`."""

    def __init__(self, path: str | Path) -> None:
        # FastAPI may open the store in one worker thread and use or close it in another.
        # Safe here: each request gets its own store and uses it sequentially.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_SCHEMA)

    def save(self, results: Iterable[TriageResult]) -> int:
        """Insert one row per result, in one transaction; return the number of rows."""
        rows = [
            (r.email_id, r.verdict.value, r.score, json.dumps([f.code for f in r.findings]))
            for r in results
        ]
        with self._conn:
            self._conn.executemany(
                "INSERT INTO verdicts (email_id, verdict, score, findings) VALUES (?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def count(self, verdict: str | None = None) -> int:
        """Count all stored verdicts, or only those equal to ``verdict``."""
        if verdict is None:
            row = self._conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()
        else:
            query = "SELECT COUNT(*) FROM verdicts WHERE verdict = ?"
            row = self._conn.execute(query, (verdict,)).fetchone()
        return int(row[0])

    def close(self) -> None:
        self._conn.close()
