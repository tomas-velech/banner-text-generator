"""
Prohlížeč historie generací.

Spuštění:
    python view_history.py            # ukáže posledních 20 generací
    python view_history.py --all      # ukáže všechny
    python view_history.py --last 5   # ukáže posledních 5
    python view_history.py --search "stavby"   # filtruje podle názvu pozice

Historie je uložena v history.db (SQLite) ve stejné složce jako aplikace.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "history.db"


def fmt_separator(char: str = "─", width: int = 78) -> str:
    return char * width


def print_record(row: sqlite3.Row) -> None:
    """Vytiskne jeden záznam v čitelné formě."""
    print(fmt_separator("═"))
    print(f"#{row['id']}  ·  {row['created_at']}  ·  model: {row['model']}", end="")
    if row["reasoning_effort"]:
        print(f"  ·  reasoning: {row['reasoning_effort']}")
    else:
        print()

    if row["input_tokens"] is not None:
        print(f"Tokeny: {row['input_tokens']} in / {row['output_tokens']} out  "
              f"·  prompt verze: {row['prompt_version']}")

    print(fmt_separator())
    print(f"NÁZEV POZICE: {row['job_title']}")

    desc = row["job_description"]
    if len(desc) > 200:
        desc = desc[:200] + "... [zkráceno]"
    print(f"POPIS: {desc}")
    print(fmt_separator())

    try:
        output = json.loads(row["output_json"])
        for v_idx, varianta in enumerate(output.get("varianty", []), start=1):
            print(f"\n  Varianta {v_idx}:")
            for b_idx in range(1, 5):
                bullet = varianta.get(f"bullet_{b_idx}", "")
                print(f"    • {bullet}  [{len(bullet)} zn.]")
    except Exception as exc:
        print(f"  [chyba parsování výstupu: {exc}]")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prohlížeč historie generací")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Zobraz všechny záznamy (default je posledních 20)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=20,
        help="Počet posledních záznamů (default 20)",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Filtr podle názvu pozice (substring, case insensitive)",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Databáze {DB_PATH} neexistuje. Vygeneruj nejprve nějaký výstup v aplikaci.")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM generations"
    params: list = []

    if args.search:
        query += " WHERE LOWER(job_title) LIKE ?"
        params.append(f"%{args.search.lower()}%")

    query += " ORDER BY id DESC"

    if not args.all:
        query += " LIMIT ?"
        params.append(args.last)

    rows = conn.execute(query, params).fetchall()
    total_count = conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]
    conn.close()

    if not rows:
        print("Žádné záznamy nenalezeny.")
        return 0

    print(f"\nCelkem v databázi: {total_count} generací")
    print(f"Zobrazeno: {len(rows)}")
    if args.search:
        print(f"Filtr: '{args.search}'")
    print()

    for row in rows:
        print_record(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
