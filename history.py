"""
SQLite ukládání historie generací a labelovacích dat pro fine-tuning.

Tabulky:
- generations        — každá vygenerovaná sada 4 variant
- bullet_ratings     — palcová hodnocení (✓/✗) jednotlivých bulletů
- approved_outputs   — schválené finální 4-bulletové sady (gold standard pro fine-tuning)

Vše běží na pozadí. UI labelovací panel je v app.py opt-in (collapsed defaultně).
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_FILENAME = "history.db"


def _db_path() -> Path:
    """Cesta k DB souboru — vedle aplikace."""
    return Path(__file__).parent / DB_FILENAME


def _now() -> str:
    """ISO timestamp v UTC, sekundová přesnost."""
    return datetime.utcnow().isoformat(timespec="seconds")


def init_db() -> None:
    """
    Vytvoří všechny tabulky, pokud neexistují. Volat při startu aplikace.
    Migrace: bezpečně přidá nové tabulky existující DB.
    """
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                model TEXT NOT NULL,
                reasoning_effort TEXT,
                job_title TEXT NOT NULL,
                job_description TEXT NOT NULL,
                output_json TEXT NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bullet_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id INTEGER NOT NULL,
                variant_idx INTEGER NOT NULL,
                bullet_idx INTEGER NOT NULL,
                rating TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (generation_id, variant_idx, bullet_idx),
                FOREIGN KEY (generation_id) REFERENCES generations (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approved_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id INTEGER NOT NULL UNIQUE,
                bullet_1 TEXT NOT NULL,
                bullet_2 TEXT NOT NULL,
                bullet_3 TEXT NOT NULL,
                bullet_4 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (generation_id) REFERENCES generations (id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#                       GENERATIONS
# ════════════════════════════════════════════════════════════

def save_generation(
    prompt_version: str,
    model: str,
    reasoning_effort: str | None,
    job_title: str,
    job_description: str,
    output: dict[str, Any],
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> int:
    """Uloží jednu generaci. Vrací ID nově vytvořeného záznamu."""
    conn = sqlite3.connect(_db_path())
    try:
        cursor = conn.execute(
            """
            INSERT INTO generations (
                created_at, prompt_version, model, reasoning_effort,
                job_title, job_description, output_json,
                input_tokens, output_tokens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                prompt_version,
                model,
                reasoning_effort,
                job_title,
                job_description,
                json.dumps(output, ensure_ascii=False),
                input_tokens,
                output_tokens,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def count_generations() -> int:
    """Vrátí celkový počet uložených generací."""
    conn = sqlite3.connect(_db_path())
    try:
        row = conn.execute("SELECT COUNT(*) FROM generations").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#                     BULLET RATINGS
# ════════════════════════════════════════════════════════════

def upsert_bullet_rating(
    generation_id: int,
    variant_idx: int,
    bullet_idx: int,
    rating: str | None,
) -> None:
    """
    Uloží/aktualizuje palcové hodnocení jednoho bulletu.

    rating: 'up' / 'down' / None (None = smaže existující hodnocení)
    """
    conn = sqlite3.connect(_db_path())
    try:
        if rating is None:
            conn.execute(
                """
                DELETE FROM bullet_ratings
                WHERE generation_id = ? AND variant_idx = ? AND bullet_idx = ?
                """,
                (generation_id, variant_idx, bullet_idx),
            )
        else:
            conn.execute(
                """
                INSERT INTO bullet_ratings
                    (generation_id, variant_idx, bullet_idx, rating, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (generation_id, variant_idx, bullet_idx) DO UPDATE SET
                    rating = excluded.rating,
                    created_at = excluded.created_at
                """,
                (generation_id, variant_idx, bullet_idx, rating, _now()),
            )
        conn.commit()
    finally:
        conn.close()


def get_bullet_ratings(generation_id: int) -> dict[tuple[int, int], str]:
    """
    Vrátí všechna uložená hodnocení pro danou generaci.

    Klíč: (variant_idx, bullet_idx), hodnota: 'up' / 'down'.
    """
    conn = sqlite3.connect(_db_path())
    try:
        rows = conn.execute(
            """
            SELECT variant_idx, bullet_idx, rating
            FROM bullet_ratings
            WHERE generation_id = ?
            """,
            (generation_id,),
        ).fetchall()
        return {(int(v), int(b)): str(r) for v, b, r in rows}
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
#                   APPROVED OUTPUTS
# ════════════════════════════════════════════════════════════

def save_approved_output(
    generation_id: int,
    bullet_1: str,
    bullet_2: str,
    bullet_3: str,
    bullet_4: str,
) -> None:
    """
    Uloží schválený 4-bulletový set jako gold standard pro fine-tuning.

    Pokud pro generation_id už existuje, přepíše se (UNIQUE constraint).
    """
    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            INSERT INTO approved_outputs
                (generation_id, bullet_1, bullet_2, bullet_3, bullet_4, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (generation_id) DO UPDATE SET
                bullet_1 = excluded.bullet_1,
                bullet_2 = excluded.bullet_2,
                bullet_3 = excluded.bullet_3,
                bullet_4 = excluded.bullet_4,
                created_at = excluded.created_at
            """,
            (generation_id, bullet_1, bullet_2, bullet_3, bullet_4, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def get_approved_output(generation_id: int) -> dict[str, str] | None:
    """Vrátí schválený set, pokud existuje. Jinak None."""
    conn = sqlite3.connect(_db_path())
    try:
        row = conn.execute(
            """
            SELECT bullet_1, bullet_2, bullet_3, bullet_4
            FROM approved_outputs
            WHERE generation_id = ?
            """,
            (generation_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "bullet_1": row[0],
            "bullet_2": row[1],
            "bullet_3": row[2],
            "bullet_4": row[3],
        }
    finally:
        conn.close()


def count_approved_outputs() -> int:
    """Kolik schválených setů máme — užitečné pro fine-tuning připravenost."""
    conn = sqlite3.connect(_db_path())
    try:
        row = conn.execute("SELECT COUNT(*) FROM approved_outputs").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()
