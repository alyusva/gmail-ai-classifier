"""
Módulo de base de datos SQLite para almacenar emails y clasificaciones.
"""
import json
import sqlite3
from contextlib import contextmanager
from typing import Optional

from loguru import logger

from . import config


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                subject TEXT,
                sender TEXT,
                sender_email TEXT,
                snippet TEXT,
                date TEXT,
                labels_original TEXT,  -- JSON array
                is_read INTEGER DEFAULT 0,
                extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS classifications (
                email_id TEXT PRIMARY KEY,
                labels TEXT,           -- JSON array de etiquetas asignadas
                confidence REAL,
                classified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                applied INTEGER DEFAULT 0,
                applied_at TEXT,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            );

            CREATE TABLE IF NOT EXISTS taxonomy (
                label TEXT PRIMARY KEY,
                gmail_label_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS progress (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
    logger.info("Base de datos inicializada en {}", config.DB_PATH)


def save_progress(key: str, value: str):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO progress (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_progress(key: str) -> Optional[str]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM progress WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None


def save_emails_batch(emails: list[dict]):
    """Inserta o actualiza un batch de emails."""
    with get_db() as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO emails
               (id, thread_id, subject, sender, sender_email, snippet, date, labels_original, is_read)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    e["id"],
                    e.get("thread_id", ""),
                    e.get("subject", "(sin asunto)"),
                    e.get("sender", ""),
                    e.get("sender_email", ""),
                    e.get("snippet", ""),
                    e.get("date", ""),
                    json.dumps(e.get("labels", [])),
                    1 if e.get("is_read") else 0,
                )
                for e in emails
            ],
        )


def get_unclassified_emails(limit: int = 50, offset: int = 0) -> list[dict]:
    """Obtiene emails que aún no han sido clasificados."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT e.id, e.subject, e.sender, e.sender_email, e.snippet, e.date
               FROM emails e
               LEFT JOIN classifications c ON e.id = c.email_id
               WHERE c.email_id IS NULL
               ORDER BY e.date DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def save_classifications(classifications: list[dict]):
    """Guarda clasificaciones en batch."""
    with get_db() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO classifications
               (email_id, labels, confidence)
               VALUES (?, ?, ?)""",
            [
                (c["email_id"], json.dumps(c["labels"]), c.get("confidence", 0.0))
                for c in classifications
            ],
        )


def mark_as_applied(email_ids: list[str]):
    """Marca emails como etiquetados en Gmail."""
    with get_db() as conn:
        conn.executemany(
            """UPDATE classifications
               SET applied = 1, applied_at = CURRENT_TIMESTAMP
               WHERE email_id = ?""",
            [(eid,) for eid in email_ids],
        )


def save_taxonomy_label(label: str, gmail_label_id: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy (label, gmail_label_id) VALUES (?, ?)",
            (label, gmail_label_id),
        )


def get_taxonomy() -> dict[str, str]:
    """Retorna {label: gmail_label_id}."""
    with get_db() as conn:
        rows = conn.execute("SELECT label, gmail_label_id FROM taxonomy").fetchall()
        return {r["label"]: r["gmail_label_id"] for r in rows}


def get_stats() -> dict:
    """Estadísticas generales."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM emails").fetchone()["c"]
        classified = conn.execute(
            "SELECT COUNT(*) as c FROM classifications"
        ).fetchone()["c"]
        applied = conn.execute(
            "SELECT COUNT(*) as c FROM classifications WHERE applied = 1"
        ).fetchone()["c"]

        # Distribución por etiqueta
        distribution = {}
        rows = conn.execute(
            "SELECT labels FROM classifications"
        ).fetchall()
        for row in rows:
            for label in json.loads(row["labels"]):
                distribution[label] = distribution.get(label, 0) + 1

        return {
            "total_emails": total,
            "classified": classified,
            "unclassified": total - classified,
            "applied": applied,
            "pending_apply": classified - applied,
            "distribution": dict(
                sorted(distribution.items(), key=lambda x: x[1], reverse=True)
            ),
        }


def get_unapplied_classifications(limit: int = 100) -> list[dict]:
    """Obtiene clasificaciones pendientes de aplicar."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.email_id, c.labels, e.subject, e.sender
               FROM classifications c
               JOIN emails e ON c.email_id = e.id
               WHERE c.applied = 0
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            {**dict(r), "labels": json.loads(r["labels"])} for r in rows
        ]


def count_emails() -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) as c FROM emails").fetchone()["c"]


def count_unclassified() -> int:
    with get_db() as conn:
        return conn.execute(
            """SELECT COUNT(*) as c FROM emails e
               LEFT JOIN classifications c ON e.id = c.email_id
               WHERE c.email_id IS NULL"""
        ).fetchone()["c"]
