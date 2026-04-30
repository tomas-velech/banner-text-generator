# Instalační návod — Generátor bullet-textů na bannery

Tento dokument popisuje krok za krokem, jak nástroj rozjet na novém počítači.

Pokrývá obě platformy:
- [Mac (macOS)](#mac--instalace)
- [Windows](#windows--instalace)

Plus navíc: [přenos souborů](#přenos-souborů-na-nový-počítač), [každodenní použití](#každodenní-spuštění-po-instalaci) a [časté problémy](#časté-problémy-a-řešení).

---

## Co tato aplikace dělá

Lokální nástroj v Pythonu se Streamlit UI. Vlož název pracovní pozice + popis, aplikace přes OpenAI API vygeneruje 4 varianty banner textů po 4 bulletech. Generace se ukládají do lokální SQLite databáze. Volitelně lze označovat finální sety pro budoucí fine-tuning.

Aplikace běží **lokálně v prohlížeči** (na adrese `http://localhost:8501`). Žádný server, žádný hosting.

---

## Než začneš — kontrolní seznam

Připravit dopředu:

- [ ] **Soubory projektu** — zip celé složky `banner-generator/` z původního počítače (postup [níže](#přenos-souborů-na-nový-počítač))
- [ ] **OpenAI API klíč** — z `https://platform.openai.com/api-keys`. Pokud klíč ještě nemáš, vygeneruj ho a překopíruj si ho někam stranou (klíč se zobrazí jen jednou)
- [ ] **Nabitý kredit na OpenAI účtu** — minimálně pár dolarů, viz `https://platform.openai.com/settings/organization/billing`
- [ ] **Administrátorská práva** k novému počítači (kvůli instalaci Pythonu)

---

## Přenos souborů na nový počítač

### Co zabalit

Z původního počítače zabal **celou složku `banner-generator/`** ALE bez:

- `venv/` — Python prostředí, je platformově specifické, vytvoříš znovu
- `__pycache__/` — kešované Python soubory, vytvoří se znovu
- `.env` — osobní API klíč, NIKDY nesdílej, vytvoříš znovu

**Volitelně přenes** soubor `history.db` — pokud chceš na novém PC zachovat historii generací a schválené sety pro fine-tuning. Bez něj začneš s prázdnou historií.

### Jak zabalit (Mac)

1. V Finderu klikni pravým tlačítkem na složku `banner-generator`
2. Před zabalením smaž složky `venv/` a `__pycache__/` (pravý klik → Move to Trash)
3. Také smaž `.env` (na novém PC vytvoříš znovu)
4. Pravý klik na složku → **Compress "banner-generator"**
5. Vznikne `banner-generator.zip`

### Jak zabalit (Windows)

1. Ve File Exploreru otevři složku `banner-generator`
2. Smaž podsložky `venv` a `__pycache__`
3. Smaž `.env`
4. Vrať se o úroveň výš, klikni pravým na `banner-generator` → **Send to** → **Compressed (zipped) folder**

### Přenos zipu

USB flash, cloudový disk (Dropbox, Google Drive, OneDrive), email — cokoli ti vyhovuje.

### Rozbalení na novém počítači

Rozbal zip na nějaké rozumné místo, např.:

- **Mac:** `/Users/tvoje-jméno/Documents/banner-generator/`
- **Windows:** `C:\Users\tvoje-jméno\Documents\banner-generator\`

---

## Mac — instalace

### Krok 1: Otevři Terminál

`Cmd + Mezerník` → napiš **Terminal** → Enter.

### Krok 2: Zkontroluj nebo nainstaluj Python

V terminálu napiš:

```bash
python3 --version
```

**Pokud uvidíš `Python 3.10.x` nebo vyšší (3.11, 3.12, 3.13...)** — pokračuj na krok 3.

**Pokud Python nemáš nebo je starý:**

1. Otevři `https://www.python.org/downloads/macos/`
2. Stáhni nejnovější verzi (klikni na velké žluté tlačítko `Download Python 3.x.x`)
3. Otevři stažený `.pkg` instalátor
4. Projdi instalací (jen klikej Pokračovat → Souhlasím → Instalovat)
5. Heslo k uživatelskému účtu si připrav, instalátor ho vyžaduje
6. Po dokončení **zavři Terminál a otevři ho znovu** (aby se aktualizovaly cesty)
7. Znovu zkus `python3 --version` — teď už by mělo fungovat

### Krok 3: Přejdi do složky s projektem

V Terminálu napiš `cd ` (cd a mezera), pak **přetáhni složku `banner-generator` z Finderu přímo do okna Terminálu** — cesta se vloží automaticky. Stiskni Enter.

Příklad výsledného příkazu:

```bash
cd "/Users/tomas.velech/Documents/banner-generator"
```

Pro ověření, že jsi ve správné složce, napiš:

```bash
ls
```

Měl bys vidět soubory `app.py`, `prompt.py`, `requirements.txt` atd.

### Krok 4: Vytvoř virtuální prostředí

```bash
python3 -m venv venv
```

Trvá pár sekund. Vznikne složka `venv/` s izolovaným Python prostředím (nebude rušit zbytek systému).

### Krok 5: Aktivuj prostředí

```bash
source venv/bin/activate
```

Před řádkem v terminálu se objeví `(venv)` — to znamená, že prostředí je aktivní.

> **Pozor:** Aktivaci budeš muset dělat při každém novém otevření Terminálu. Když Terminál zavřeš a otevřeš nový, znovu `cd` do složky a `source venv/bin/activate`.

### Krok 6: Nainstaluj balíčky

```bash
pip install -r requirements.txt
```

Stáhne se Streamlit, OpenAI SDK a python-dotenv. Trvá to 30 s až 2 minuty podle rychlosti internetu. Hláška o nové verzi pip na konci je v pořádku, můžeš ji ignorovat.

### Krok 7: Vytvoř soubor `.env` s API klíčem

```bash
cp .env.example .env
open .env
```

Otevře se soubor v defaultním textovém editoru macOS. Uvidíš:

```
OPENAI_API_KEY=sk-your-api-key-here
```

Nahraď `sk-your-api-key-here` svým skutečným API klíčem (začíná `sk-...`). Ulož (`Cmd + S`) a zavři okno editoru.

### Krok 8: Spusť aplikaci

```bash
streamlit run app.py
```

V Terminálu uvidíš:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

A automaticky se aplikace otevře v defaultním prohlížeči. Pokud ne, otevři adresu ručně.

**Při úplně prvním spuštění Streamlitu** se zeptá na email — pole nech prázdné a stiskni Enter.

### Krok 9: Ukončení aplikace

V Terminálu stiskni `Ctrl + C`. Aplikace se zastaví, ale virtuální prostředí stále běží.

---

## Windows — instalace

### Krok 1: Otevři PowerShell

Stiskni klávesu `Win` (nebo Win+R), napiš **PowerShell** a stiskni Enter.

> **Tip:** Pokud máš novější Windows 11, doporučuji **Windows Terminal** z Microsoft Store — je to hezčí PowerShell. Není to ale podmínka.

### Krok 2: Zkontroluj nebo nainstaluj Python

V PowerShellu napiš:

```powershell
python --version
```

**Pokud uvidíš `Python 3.10.x` nebo vyšší** — pokračuj na krok 3.

**Pokud Python nemáš nebo je starý:**

1. Otevři `https://www.python.org/downloads/windows/`
2. Stáhni **Windows installer (64-bit)** nejnovější Python 3.x verze
3. Spusť stažený `.exe` instalátor
4. ⚠️ **DŮLEŽITÉ:** Na první obrazovce instalátoru zaškrtni checkbox **„Add python.exe to PATH"** (úplně dole). Bez něj instalace nebude fungovat — Windows nebude vědět, kde Python hledat.
5. Klikni **Install Now**
6. Po dokončení **zavři PowerShell a otevři ho znovu**
7. Znovu zkus `python --version`

### Krok 3: Přejdi do složky s projektem

Ve File Exploreru otevři složku `banner-generator`, klikni do adresního řádku nahoře (zobrazí se cesta), zkopíruj ji (`Ctrl + C`).

V PowerShellu napiš `cd ` (s mezerou) a vlož cestu (`Ctrl + V`). Použij uvozovky kolem cesty, pokud obsahuje mezery:

```powershell
cd "C:\Users\tomas.velech\Documents\banner-generator"
```

Stiskni Enter. Pro ověření napiš `dir` — měl bys vidět všechny soubory projektu.

### Krok 4: Vytvoř virtuální prostředí

```powershell
python -m venv venv
```

Trvá pár sekund. Vznikne složka `venv\` s izolovaným Python prostředím.

### Krok 5: Aktivuj prostředí

```powershell
venv\Scripts\Activate.ps1
```

Před řádkem se objeví `(venv)` — prostředí je aktivní.

#### Když uvidíš chybu „running scripts is disabled on this system"

PowerShell má defaultně zakázané spouštění lokálních skriptů. Spusť (jednorázově):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

PowerShell se zeptá na potvrzení — napiš `Y` a Enter. Pak znovu zkus aktivaci `venv\Scripts\Activate.ps1`.

#### Pokud používáš Command Prompt místo PowerShellu

Aktivace má jiný příkaz:

```cmd
venv\Scripts\activate.bat
```

> **Pozor:** Aktivaci budeš muset dělat při každém novém otevření PowerShellu. Když ho zavřeš a otevřeš nový, znovu `cd` do složky a `venv\Scripts\Activate.ps1`.

### Krok 6: Nainstaluj balíčky

```powershell
pip install -r requirements.txt
```

Trvá 30 s až 2 minuty.

### Krok 7: Vytvoř soubor `.env` s API klíčem

```powershell
copy .env.example .env
notepad .env
```

Otevře se Notepad se souborem. Uvidíš:

```
OPENAI_API_KEY=sk-your-api-key-here
```

Nahraď `sk-your-api-key-here` skutečným API klíčem. Ulož (`Ctrl + S`) a zavři Notepad.

### Krok 8: Spusť aplikaci

```powershell
streamlit run app.py
```

V PowerShellu uvidíš adresu `http://localhost:8501`. Aplikace se automaticky otevře v defaultním prohlížeči.

**Při úplně prvním spuštění Streamlitu** se tě zeptá na email — Enter, pole nech prázdné.

### Krok 9: Ukončení aplikace

V PowerShellu `Ctrl + C`.

---

## Každodenní spuštění (po instalaci)

Když chceš jen aplikaci spustit (Python a balíčky už máš nainstalované), stačí 3 příkazy.

### Mac

```bash
cd "/cesta/k/banner-generator"
source venv/bin/activate
streamlit run app.py
```

### Windows (PowerShell)

```powershell
cd "C:\cesta\k\banner-generator"
venv\Scripts\Activate.ps1
streamlit run app.py
```

### Tip: vytvoř si zástupce

Místo opakovaného psaní příkazů si můžeš vytvořit jednoduchý spouštěcí skript:

**Mac (vytvoř soubor `start.command` ve složce s projektem):**

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run app.py
```

Pak `chmod +x start.command` (jednou). Dvojklik v Finderu spustí.

**Windows (vytvoř soubor `start.bat` ve složce s projektem):**

```bat
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run app.py
```

Dvojklikem v File Exploreru spustí.

---

## Časté problémy a řešení

### „ModuleNotFoundError: No module named 'streamlit'" (po `streamlit run app.py`)

Nemáš aktivované virtuální prostředí. Před řádkem v terminálu by mělo být `(venv)`. Pokud ne, znovu aktivuj:

- Mac: `source venv/bin/activate`
- Windows: `venv\Scripts\Activate.ps1`

### „Chybí OPENAI_API_KEY"

Soubor `.env` ve složce s projektem neexistuje, nebo neobsahuje klíč. Otevři ho v editoru a zkontroluj, že tam je:

```
OPENAI_API_KEY=sk-...
```

Bez uvozovek, bez mezer kolem `=`.

### Aplikace se neotevře v prohlížeči

Otevři adresu `http://localhost:8501` ručně. Pokud Streamlit hlásil jinou (např. `:8502`), použij tu.

### Port 8501 je obsazený

Streamlit automaticky zkusí 8502, 8503, 8504... Sleduj výstup v terminálu, kde se ti vypíše skutečná URL.

### Python příkazy nefungují (Windows): „python is not recognized"

Při instalaci jsi nezaškrtl **„Add Python to PATH"**. Odinstaluj Python (Settings → Apps → Python → Uninstall) a nainstaluj znovu s tím checkboxem zaškrtnutým.

### „running scripts is disabled" (Windows PowerShell)

Spusť:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Potvrď `Y`. Pak znovu zkus aktivaci.

### Pomalé generování (40+ s)

To je normální chování reasoning modelů (`gpt-5.5`, `gpt-5.4`). Zkus přepnout na `gpt-5.3-chat-latest` v dropdownu — je výrazně rychlejší (~10 s), kvalita je o trochu nižší ale často dostatečná.

### „API klíč je neplatný" / „Insufficient quota"

Zkontroluj, že máš na OpenAI účtu nabitý kredit:
`https://platform.openai.com/settings/organization/billing`

Pokud je kredit, zkus vygenerovat nový API klíč (`https://platform.openai.com/api-keys`) a aktualizovat `.env`.

### Aplikace nefunguje po restartu počítače

To je v pořádku. Po restartu je virtuální prostředí stále nainstalované, ale není aktivované. Spusť znovu příkazy z [Každodenní spuštění](#každodenní-spuštění-po-instalaci).

### Chyba u importu při spuštění Streamlitu

Pravděpodobně chybí některý balíček. Spusť znovu:

```bash
pip install -r requirements.txt
```

V aktivovaném prostředí.

---

## Aktualizace nástroje (když na původním PC něco upravíš)

Když na původním Macu změníš kód (např. v `prompt.py` nebo `app.py`) a chceš to mít i na druhém zařízení:

1. Zkopíruj upravené soubory (např. přes USB / cloud)
2. Nahraď je v projektové složce na novém PC
3. Pokud se změnil `requirements.txt`, v aktivovaném prostředí spusť `pip install -r requirements.txt`
4. Restartuj Streamlit (`Ctrl + C`, znovu `streamlit run app.py`)

> Pro pohodlnější dlouhodobou synchronizaci zvaž použití Gitu (GitHub) — kód uložíš do repozitáře a na druhém PC stahuješ změny příkazem `git pull`. To je ale nadstavba mimo rozsah tohoto návodu.

---

## Užitečné odkazy

- OpenAI API klíče: `https://platform.openai.com/api-keys`
- OpenAI fakturace: `https://platform.openai.com/settings/organization/billing`
- OpenAI Playground (pro testování modelů): `https://platform.openai.com/playground`
- Python download: `https://www.python.org/downloads/`
- Streamlit dokumentace: `https://docs.streamlit.io`

---

## Co všechno je v projektu

```
banner-generator/
├── app.py                       # Streamlit UI
├── prompt.py                    # Hlavní prompt (V1-V4)
├── openai_client.py             # Volání OpenAI API
├── history.py                   # SQLite — generations, ratings, approved sets
├── view_history.py              # Skript pro prohlížení historie
├── export_for_finetuning.py     # Skript pro export trénovacích dat (JSONL)
├── requirements.txt             # Python závislosti
├── .env                         # Tvůj API klíč (vytváříš sám)
├── .env.example                 # Šablona pro .env
├── .gitignore
├── history.db                   # SQLite databáze (vznikne automaticky)
├── README.md                    # Stručný přehled
└── INSTALL.md                   # Tento návod
```

Pokud chceš změnit prompt, uprav `prompt.py` a restartuj aplikaci. Pokud chceš změnit dropdown s modely, uprav `AVAILABLE_MODELS` v `openai_client.py`.
