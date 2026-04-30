"""
Generátor bullet-textů na bannery pracovních inzerátů.

Spuštění:
    streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv

from history import (
    count_approved_outputs,
    get_approved_output,
    get_bullet_ratings,
    init_db,
    save_approved_output,
    save_generation,
    upsert_bullet_rating,
)
from openai_client import (
    AVAILABLE_MODELS,
    DEFAULT_REASONING_EFFORT,
    REASONING_EFFORT_OPTIONS,
    generate_variants,
)
from prompt import PROMPT_VERSION

# Načti API klíč z .env při startu
load_dotenv()

# Inicializuj DB při startu (idempotentní — vytvoří chybějící tabulky)
init_db()

# ───────── konfigurace stránky ─────────
st.set_page_config(
    page_title="Generátor bullet-textů na bannery",
    page_icon="📢",
    layout="centered",
)

st.title("Generátor bullet-textů na bannery")
st.caption(
    "Vlož název pozice a popis pracovní nabídky. "
    "Nástroj vygeneruje 4 varianty po 4 bulletech."
)

# ───────── vstupní formulář ─────────
with st.form("input_form"):
    job_title = st.text_input(
        "Název pozice",
        placeholder="např. Stavbyvedoucí / Mistři",
    )

    job_description = st.text_area(
        "Popis pozice",
        height=300,
        placeholder=(
            "Vlož sem celý text pracovního inzerátu "
            "(klidně i s HTML — model si s tím poradí)..."
        ),
    )

    col_model, col_effort = st.columns(2)
    with col_model:
        model = st.selectbox(
            "Model",
            options=AVAILABLE_MODELS,
            index=0,
            help="Vyšší modely = lepší kvalita, vyšší cena.",
        )
    with col_effort:
        reasoning_effort = st.selectbox(
            "Reasoning effort",
            options=REASONING_EFFORT_OPTIONS,
            index=REASONING_EFFORT_OPTIONS.index(DEFAULT_REASONING_EFFORT),
            help=(
                "Kolik 'přemýšlení' model použije před odpovědí. "
                "Vyšší = kvalitnější, pomalejší, dražší. "
                "Aplikuje se jen na reasoning modely (gpt-5.x, o-series)."
            ),
        )

    submitted = st.form_submit_button("Generovat", type="primary")

# ───────── generování ─────────
if submitted:
    if not job_title.strip() or not job_description.strip():
        st.error("Vyplň prosím oba vstupy — název i popis pozice.")
    else:
        with st.spinner("Generuji 4 varianty..."):
            try:
                result = generate_variants(
                    job_title=job_title,
                    job_description=job_description,
                    model=model,
                    reasoning_effort=reasoning_effort,
                )
            except Exception as exc:
                st.error(f"Chyba při generování: {exc}")
                st.stop()

        # Ulož na pozadí — selhání nesmí shodit zobrazení
        new_generation_id: int | None = None
        try:
            new_generation_id = save_generation(
                prompt_version=PROMPT_VERSION,
                model=result["_meta"]["model"],
                reasoning_effort=result["_meta"]["reasoning_effort"],
                job_title=job_title,
                job_description=job_description,
                output={"varianty": result["varianty"]},
                input_tokens=result["_meta"]["input_tokens"],
                output_tokens=result["_meta"]["output_tokens"],
            )
        except Exception as exc:
            st.warning(f"Generace proběhla, ale uložení do historie selhalo: {exc}")

        # Reset labelovacích polí pro novou generaci
        for slot in range(1, 5):
            st.session_state[f"final_b{slot}"] = ""

        st.session_state["last_result"] = result
        st.session_state["last_generation_id"] = new_generation_id


# ───────── callbacky pro labeling ─────────

def _on_rating_change(generation_id: int, v_idx: int, b_idx: int, widget_key: str) -> None:
    """Volá se při změně palcového hodnocení — uloží do DB."""
    if generation_id is None:
        return
    value = st.session_state.get(widget_key, "—")
    rating_map = {"👍": "up", "👎": "down", "—": None}
    rating = rating_map.get(value)
    upsert_bullet_rating(generation_id, v_idx, b_idx, rating)


def _use_bullet_in_slot(slot: int, bullet_text: str) -> None:
    """Klik na '→ Bx' tlačítko: nastaví text v cílovém slotu finálního setu."""
    st.session_state[f"final_b{slot}"] = bullet_text


# ───────── výpis výsledku ─────────
if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    varianty = result["varianty"]
    meta = result["_meta"]
    generation_id = st.session_state.get("last_generation_id")

    st.divider()
    st.subheader("Výsledek")

    # malá info lišta s metadaty
    info_parts = [f"Model: `{meta['model']}`"]
    if meta.get("reasoning_effort"):
        info_parts.append(f"Reasoning: `{meta['reasoning_effort']}`")
    if meta.get("input_tokens") is not None:
        info_parts.append(
            f"Tokeny: {meta['input_tokens']} in / {meta['output_tokens']} out"
        )
    st.caption(" · ".join(info_parts))

    # 4 varianty pod sebou
    for idx, varianta in enumerate(varianty, start=1):
        with st.container(border=True):
            st.markdown(f"**Varianta {idx}**")
            for bullet_idx in range(1, 5):
                bullet_text = varianta.get(f"bullet_{bullet_idx}", "")
                char_count = len(bullet_text)
                col_text, col_count = st.columns([10, 1])
                with col_text:
                    st.code(bullet_text, language=None)
                with col_count:
                    st.caption(f"{char_count}")

            # Kompletní varianta — všechny 4 bullety najednou ke zkopírování
            full_text = "\n".join(
                varianta.get(f"bullet_{i}", "") for i in range(1, 5)
            )
            with st.expander("Kopírovat celou variantu (4 bullety najednou)"):
                st.code(full_text, language=None)

    # ═══════════════════════════════════════════════════════
    # OPT-IN PANEL: označení a sestavení finálního setu
    # ═══════════════════════════════════════════════════════
    st.divider()

    approved_count = count_approved_outputs()
    panel_title = (
        f"▸ Označit a sestavit finální set pro fine-tuning "
        f"(zatím schválených: {approved_count})"
    )

    with st.expander(panel_title, expanded=False):
        if generation_id is None:
            st.info(
                "Tato generace se nepodařila uložit do historie, "
                "labelování není dostupné."
            )
        else:
            st.markdown(
                "**Per-bullet hodnocení.** Označuj jen ty, kde máš jasný názor — "
                "ostatní můžeš nechat neutrální. Hodnocení se ukládá automaticky."
            )

            existing_ratings = get_bullet_ratings(generation_id)

            # Pro každou variantu řádek bulletů s ratingem a "Použít jako" tlačítky
            for v_idx, varianta in enumerate(varianty, start=1):
                st.markdown(f"_Varianta {v_idx}:_")
                for b_idx in range(1, 5):
                    bullet_text = varianta.get(f"bullet_{b_idx}", "")

                    # Stávající rating z DB (pokud je)
                    saved = existing_ratings.get((v_idx, b_idx))
                    rating_to_emoji = {"up": "👍", "down": "👎"}
                    default_emoji = rating_to_emoji.get(saved, "—")

                    cols = st.columns([8, 2, 1, 1, 1, 1])

                    with cols[0]:
                        st.text(bullet_text)

                    widget_key = f"rating_{generation_id}_{v_idx}_{b_idx}"
                    with cols[1]:
                        st.radio(
                            "Hodnocení",
                            options=["—", "👍", "👎"],
                            index=["—", "👍", "👎"].index(default_emoji),
                            horizontal=True,
                            key=widget_key,
                            label_visibility="collapsed",
                            on_change=_on_rating_change,
                            args=(generation_id, v_idx, b_idx, widget_key),
                        )

                    # 4 tlačítka "→Bx" — pošlou bullet do slotu finálního setu
                    for slot in range(1, 5):
                        with cols[1 + slot]:
                            st.button(
                                f"→B{slot}",
                                key=f"use_{generation_id}_{v_idx}_{b_idx}_b{slot}",
                                on_click=_use_bullet_in_slot,
                                args=(slot, bullet_text),
                                help=f"Použít tento bullet jako B{slot} ve finálním setu",
                            )

            st.divider()
            st.markdown(
                "**Finální set.** Klikáním na tlačítka „→ Bx\" naplníš sloty výše. "
                "Texty pak můžeš libovolně doupravit. Uložením potvrdíš gold standard "
                "pro fine-tuning."
            )

            # 4 editovatelné sloty
            for slot in range(1, 5):
                key = f"final_b{slot}"
                if key not in st.session_state:
                    st.session_state[key] = ""
                st.text_input(
                    f"B{slot}",
                    key=key,
                )

            col_save, col_clear = st.columns([1, 1])
            with col_save:
                if st.button("Uložit schválený set", type="primary"):
                    bullets = [st.session_state[f"final_b{i}"] for i in range(1, 5)]
                    if all(b.strip() for b in bullets):
                        save_approved_output(
                            generation_id,
                            bullets[0],
                            bullets[1],
                            bullets[2],
                            bullets[3],
                        )
                        st.success(
                            f"Uloženo! Celkem schválených setů: "
                            f"{count_approved_outputs()}"
                        )
                    else:
                        st.error("Všechny 4 sloty musí být vyplněné.")
            with col_clear:
                if st.button("Vyprázdnit sloty"):
                    for slot in range(1, 5):
                        st.session_state[f"final_b{slot}"] = ""
                    st.rerun()

            # Pokud už existuje schválený set, ukaž poznámku
            existing = get_approved_output(generation_id)
            if existing:
                st.info(
                    "Pro tuto generaci už existuje uložený schválený set. "
                    "Uložením znovu se přepíše."
                )
