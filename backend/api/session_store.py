# backend/api/session_store.py
"""
SQLite-backed session and message history store.

Provides durable, server-side conversation memory across page refreshes
and container restarts (SQLite file is volume-mounted in Docker).

Schema:
    sessions  (id, created_at, last_active_at)
    messages  (id, session_id, role, content, timestamp)

Thread safety: sqlite3 with WAL mode — safe for FastAPI's single-worker setup.
For multi-worker deployments, switch to PostgreSQL via SQLAlchemy async.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


class SessionStore:
    """
    Lightweight SQLite session manager.

    All operations are synchronous and fast (sub-millisecond on local SSD).
    Safe to call directly from FastAPI async endpoints — SQLite I/O on a
    locally-mounted file does not meaningfully block the event loop.
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"SessionStore ready at '{db_path}'")

    # ── Connection & schema ────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Safe concurrent reads
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id             TEXT PRIMARY KEY,
                    created_at     TEXT NOT NULL,
                    last_active_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT    NOT NULL,
                    role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
                    content    TEXT    NOT NULL,
                    timestamp  TEXT    NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                    ON messages(session_id, id);
            """)

    # ── Session lifecycle ──────────────────────────────────────────────

    def create_session(self) -> str:
        """Create a new session. Returns the new session_id (UUID hex)."""
        session_id = uuid.uuid4().hex
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(id, created_at, last_active_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
        logger.debug(f"Session created: {session_id}")
        return session_id

    def session_exists(self, session_id: str) -> bool:
        """Return True if this session_id exists in the DB."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row is not None

    def get_or_create_session(self, session_id: Optional[str]) -> str:
        """
        Return an existing session_id if valid, or create a new one.

        Args:
            session_id: Client-provided ID (from localStorage). None = new session.

        Returns:
            A valid session_id string.
        """
        if session_id and self.session_exists(session_id):
            self._touch(session_id)
            return session_id
        return self.create_session()

    def _touch(self, session_id: str) -> None:
        """Update last_active_at to now."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET last_active_at = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), session_id),
            )

    # ── Message operations ─────────────────────────────────────────────

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Append one message to a session.

        Args:
            session_id: Target session
            role:       'user' or 'assistant'
            content:    Message text
        """
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages(session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, now),
            )
            conn.execute(
                "UPDATE sessions SET last_active_at = ? WHERE id = ?",
                (now, session_id),
            )

    def add_turn(
        self, session_id: str, user_message: str, assistant_message: str
    ) -> None:
        """Convenience method: add a user + assistant turn in one call."""
        self.add_message(session_id, "user", user_message)
        self.add_message(session_id, "assistant", assistant_message)

    def get_history(
        self,
        session_id: str,
        last_n_turns: int = 5,
    ) -> List[Tuple[str, str]]:
        """
        Load the last N conversation turns for a session.

        Args:
            session_id:  Session to query
            last_n_turns: Number of (user, assistant) pairs to return

        Returns:
            List of (user_message, assistant_message) tuples, oldest first.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content
                FROM   messages
                WHERE  session_id = ?
                ORDER  BY id DESC
                LIMIT  ?
                """,
                (session_id, last_n_turns * 2),
            ).fetchall()

        # Rows are newest-first; reverse to chronological
        rows = list(reversed(rows))

        # Pair consecutive user + assistant messages
        turns: List[Tuple[str, str]] = []
        i = 0
        while i < len(rows) - 1:
            if rows[i]["role"] == "user" and rows[i + 1]["role"] == "assistant":
                turns.append((rows[i]["content"], rows[i + 1]["content"]))
                i += 2
            else:
                i += 1  # Skip unpaired message (edge case)

        return turns

    def get_full_history(self, session_id: str) -> List[dict]:
        """Return all messages in a session as a list of {role, content, timestamp} dicts."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ── Management ────────────────────────────────────────────────────

    def clear_session(self, session_id: str) -> int:
        """Delete all messages for a session. Returns deleted message count."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM messages WHERE session_id = ?", (session_id,)
            )
            return cursor.rowcount

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages. Returns True if found."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Return metadata about a session, or None if not found."""
        with self._connect() as conn:
            session = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not session:
                return None
            msg_count = conn.execute(
                "SELECT COUNT(*) as n FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()["n"]

        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "last_active": session["last_active_at"],
            "message_count": msg_count,
            "turn_count": msg_count // 2,
        }

    def global_stats(self) -> dict:
        """Store-wide statistics."""
        with self._connect() as conn:
            sessions = conn.execute("SELECT COUNT(*) as n FROM sessions").fetchone()[
                "n"
            ]
            messages = conn.execute("SELECT COUNT(*) as n FROM messages").fetchone()[
                "n"
            ]
        return {
            "total_sessions": sessions,
            "total_messages": messages,
        }
