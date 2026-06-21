import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from decimal import Decimal

DB_PATH = Path(__file__).parent.parent / "data" / "interactions.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Call once at app startup."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                raw_input   TEXT,
                merchant    TEXT,
                amount      TEXT,
                currency    TEXT,
                tx_type     TEXT,
                confidence  TEXT,
                explanation TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id             TEXT PRIMARY KEY,
                interaction_id TEXT NOT NULL REFERENCES interactions(id),
                session_id     TEXT NOT NULL,
                timestamp      TEXT NOT NULL,
                accepted       INTEGER NOT NULL  -- 1 = thumbs up, 0 = thumbs down
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id             TEXT PRIMARY KEY,
                session_id     TEXT NOT NULL,
                timestamp      TEXT NOT NULL,
                message        TEXT
            )
        """)
        conn.commit()


def log_interaction(
    session_id: str,
    raw_input: str,
    result,          # TranslatedTransaction
) -> str:
    """Log one agent response. Returns the interaction ID."""
    interaction_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    amount_str = f"{result.amount:.2f}" if result.amount is not None else None

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO interactions
                (id, session_id, timestamp, raw_input,
                 merchant, amount, currency, tx_type, confidence, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction_id, session_id, now, raw_input,
                result.merchant,
                amount_str,
                result.currency,
                result.transaction_type.value if result.transaction_type else None,
                result.confidence.value if result.confidence else None,
                result.plain_english_explanation,
            ),
        )
        conn.commit()
    return interaction_id


def log_feedback(session_id: str, interaction_id: str, accepted: bool) -> None:
    """Call this when the user presses thumbs-up or thumbs-down."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feedback (id, interaction_id, session_id, timestamp, accepted)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), interaction_id, session_id, datetime.utcnow().isoformat(), int(accepted)),
        )
        conn.commit()


def log_followup(session_id: str, message: str) -> None:
    """Call this when a user sends a second message in the same session."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO followups (id, session_id, timestamp, message) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, datetime.utcnow().isoformat(), message),
        )
        conn.commit()


def compute_kpis() -> dict:
    """Return current values for all three business KPIs."""
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        if total == 0:
            return {"acceptance_rate": None, "clarification_rate": None, "coverage_rate": None}

        # Acceptance rate
        accepted = conn.execute("SELECT COUNT(*) FROM feedback WHERE accepted = 1").fetchone()[0]
        total_feedback = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        acceptance_rate = round(accepted / total_feedback, 4) if total_feedback else None

        # Clarification rate
        sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM interactions").fetchone()[0]
        flagged_sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM followups").fetchone()[0]
        clarification_rate = round(flagged_sessions / sessions, 4) if sessions else None

        # Coverage rate (high or medium confidence)
        covered = conn.execute(
            "SELECT COUNT(*) FROM interactions WHERE confidence IN ('high', 'medium')"
        ).fetchone()[0]
        coverage_rate = round(covered / total, 4) if total else None

    return {
        "acceptance_rate":   acceptance_rate,
        "clarification_rate": clarification_rate,
        "coverage_rate":      coverage_rate,
        "total_interactions": total,
        "total_feedback":     total_feedback,
    }