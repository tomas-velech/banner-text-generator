"""
Export schválených setů do JSONL formátu pro OpenAI fine-tuning.

Strategie (Cesta Y):
- Trénujeme model přímo na 4-bulletový gold-standard set (ne na 4 varianty).
- Vstupem je název pozice + popis pozice, výstupem 4 bullety v JSON.
- Po fine-tuningu by model rovnou produkoval „nejlepší" 4 bullety, bez nutnosti
  cherry-pickingu napříč variantami.

Spuštění:
    python export_for_finetuning.py > training.jsonl
    python export_for_finetuning.py --validate                # jen kontrola
    python export_for_finetuning.py --output training.jsonl   # do souboru

OpenAI doporučuje minimálně 50 příkladů pro fine-tuning, ideálně 100+.
Skript při startu vypíše počet příkladů a varování, pokud je jich málo.

Kompatibilní formát: chat completions JSONL podle
https://platform.openai.com/docs/guides/fine-tuning
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "history.db"

# Lean fine-tune system prompt — kratší, bez few-shot příkladů.
# Po fine-tuningu model bude vědět styl z trénovacích dat.
SYSTEM_PROMPT_FT = """Jsi seniorní kreativní copywriter pro pracovní inzeráty na sociálních sítích. Pracuješ pouze s informacemi z přiloženého inzerátu, nic si nevymýšlíš.

Vygeneruj 4 nejlepší bullety pro banner pracovního inzerátu:
- BULLET 1 — Háček o roli (typicky: Postaráte se / Stanete se / Zajistíte / Posílíte / Převezmete)
- BULLET 2 — Konkrétní náplň práce nebo hlavní zodpovědnost
- BULLET 3 — Klíčový požadavek (typicky: Máte / Potřebujete / Využijete)
- BULLET 4 — Hlavní benefit nebo odměna (typicky: Získáte / Nabízíme / imperativ)

Pravidla:
- Cílová délka 50–55 znaků včetně mezer, hard limit 55. Využívej maximum.
- 2. osoba, budoucí čas pro popis role a benefitů, přítomný pro požadavky.
- Vykání nebo tykání podle stylu inzerátu (konzistentně napříč všemi 4 bullety).
- Žádné emoji, otazníky, vykřičníky, tečky na konci.
- Žádný název města, žádná základní mzda z hlavičky inzerátu.
- Specifické bonusy povolené: 13./14. plat, náborový bonus, prémie, příspěvky.

Výstup pouze validní JSON:
{"bullet_1": "...", "bullet_2": "...", "bullet_3": "...", "bullet_4": "..."}
"""


def build_user_message(job_title: str, job_description: str) -> str:
    return f"NÁZEV POZICE: {job_title}\n\nPOPIS POZICE:\n{job_description}"


def fetch_training_pairs() -> list[dict]:
    """Načte všechny schválené sety s odpovídajícími generacemi."""
    if not DB_PATH.exists():
        print(f"ERROR: databáze {DB_PATH} neexistuje.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT g.job_title, g.job_description,
                   a.bullet_1, a.bullet_2, a.bullet_3, a.bullet_4
            FROM approved_outputs a
            JOIN generations g ON g.id = a.generation_id
            ORDER BY a.id
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def build_training_example(pair: dict) -> dict:
    """Sestaví jeden chat completions training example."""
    assistant_output = {
        "bullet_1": pair["bullet_1"],
        "bullet_2": pair["bullet_2"],
        "bullet_3": pair["bullet_3"],
        "bullet_4": pair["bullet_4"],
    }
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_FT},
            {
                "role": "user",
                "content": build_user_message(
                    pair["job_title"], pair["job_description"]
                ),
            },
            {
                "role": "assistant",
                "content": json.dumps(assistant_output, ensure_ascii=False),
            },
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Cesta k výstupnímu souboru. Pokud není zadána, tiskne na stdout.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Jen ověř data a vypiš statistiku, nic neexportuj.",
    )
    args = parser.parse_args()

    pairs = fetch_training_pairs()
    count = len(pairs)

    print(f"Schválených setů v DB: {count}", file=sys.stderr)

    if count == 0:
        print(
            "Žádné schválené sety. V aplikaci klikni na panel "
            "\"Označit a sestavit finální set pro fine-tuning\" a sestav alespoň "
            "1 set, aby bylo co exportovat.",
            file=sys.stderr,
        )
        return 1

    if count < 50:
        print(
            f"VAROVÁNÍ: OpenAI doporučuje minimálně 50 příkladů, máš jen {count}. "
            f"Fine-tuning teď proběhne, ale výsledná kvalita může být slabá.",
            file=sys.stderr,
        )
    elif count < 100:
        print(
            f"INFO: Máš {count} příkladů — to už by mělo stačit, ale 100+ je ideál.",
            file=sys.stderr,
        )
    else:
        print(f"OK: {count} příkladů — dobré množství pro fine-tuning.", file=sys.stderr)

    if args.validate:
        print("Validace OK. Spuštění bez --validate provede export.", file=sys.stderr)
        return 0

    examples = [build_training_example(p) for p in pairs]
    output_lines = [json.dumps(ex, ensure_ascii=False) for ex in examples]

    if args.output:
        path = Path(args.output)
        path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        print(f"Zapsáno: {path}", file=sys.stderr)
    else:
        for line in output_lines:
            print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
