# Generátor bullet-textů na bannery

Lokální nástroj pro generování textů na bannery pracovních inzerátů přes OpenAI API.

## Co to dělá

Vložíš název pozice a text pracovního inzerátu, nástroj vygeneruje **4 varianty po 4 bulletech**, každý ve formátu vhodném pro banner sociálních sítí (40–52 znaků). Generace běží přes OpenAI API, prompt je vyladěn na základě historických dat.

## První spuštění (jednorázově)

### 1. Nainstaluj Python

Pokud ještě nemáš, stáhni Python 3.10 nebo novější z [python.org](https://www.python.org/downloads/).

### 2. Otevři terminál ve složce s projektem

```bash
cd "/Users/tomas.velech/Text creator/banner-generator"
```

### 3. (Doporučeno) Vytvoř virtuální prostředí

Tím se izolují balíčky tohoto projektu od zbytku systému:

```bash
python3 -m venv venv
source venv/bin/activate
```

Při dalším spuštění aplikace už stačí jen ten druhý řádek (`source venv/bin/activate`).

### 4. Nainstaluj balíčky

```bash
pip install -r requirements.txt
```

### 5. Vlož svůj OpenAI API klíč

Zkopíruj soubor `.env.example` jako `.env`:

```bash
cp .env.example .env
```

Otevři `.env` v editoru a nahraď `sk-your-api-key-here` svým skutečným klíčem z [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

## Spuštění aplikace

```bash
streamlit run app.py
```

Otevře se ti v prohlížeči (typicky na `http://localhost:8501`). Pokud ne, otevři tu adresu sám.

Ukončit aplikaci: v terminálu `Ctrl + C`.

## Co je v aplikaci

- **Název pozice** — např. „Stavbyvedoucí"
- **Popis pozice** — celý text inzerátu, klidně i s HTML
- **Model** — výchozí `gpt-5.5`, alternativy pro porovnání ceny/kvality
- **Reasoning effort** — kolik „přemýšlení" model použije (low/medium/high)
- **Generovat** — vygeneruje 4 varianty pod formulářem

## Historie

Všechny generace se ukládají na pozadí do souboru `history.db` (SQLite) v této složce. UI je nezobrazuje, ale data jsou připravená pro budoucí ladění promptu nebo fine-tuning.

## Struktura projektu

```
banner-generator/
├── app.py              # Streamlit UI
├── prompt.py           # Prompt v2 + JSON schema
├── openai_client.py    # Volání OpenAI API
├── history.py          # SQLite ukládání
├── .env                # API klíč (vytvoříš sám, ne v gitu)
├── .env.example        # Šablona pro .env
├── .gitignore
├── requirements.txt    # Python závislosti
├── history.db          # SQLite databáze (vznikne automaticky)
└── README.md
```

## Náklady

OpenAI účtuje podle počtu tokenů. Jedna generace typicky stojí jednotky centů. Aktuální spotřebu uvidíš pod každým výsledkem.

## Změna promptu

Prompt je v `prompt.py` jako konstanta `SYSTEM_PROMPT`. Stačí ho upravit a aplikaci restartovat.
