import sqlite3
from datetime import datetime, timezone


class Storage:
    def __init__(self, path: str = "news_parser.db"):
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                chat_title TEXT,
                posted_at TEXT NOT NULL,
                text TEXT,
                link TEXT,
                PRIMARY KEY (chat_id, message_id)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                reasoning TEXT,
                matched_at TEXT NOT NULL,
                PRIMARY KEY (chat_id, message_id),
                FOREIGN KEY (chat_id, message_id)
                    REFERENCES messages (chat_id, message_id)
            )
            """
        )
        self._conn.commit()

    def save_message(self, chat_id: int, message_id: int, chat_title: str,
                      posted_at: datetime, text: str, link: str):
        self._conn.execute(
            """
            INSERT OR IGNORE INTO messages
                (chat_id, message_id, chat_title, posted_at, text, link)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, message_id, chat_title, posted_at.isoformat(), text, link),
        )
        self._conn.commit()

    def save_match(self, chat_id: int, message_id: int, reasoning: str):
        self._conn.execute(
            """
            INSERT OR IGNORE INTO matches (chat_id, message_id, reasoning, matched_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, message_id, reasoning, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def matches_in_range(self, start: datetime, end: datetime):
        cur = self._conn.execute(
            """
            SELECT m.chat_title, m.posted_at, m.text, m.link, x.reasoning
            FROM matches x
            JOIN messages m ON m.chat_id = x.chat_id AND m.message_id = x.message_id
            WHERE m.posted_at BETWEEN ? AND ?
            ORDER BY m.posted_at ASC
            """,
            (start.isoformat(), end.isoformat()),
        )
        return cur.fetchall()

    def close(self):
        self._conn.close()
