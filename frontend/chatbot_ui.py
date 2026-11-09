"""Page « Assistant IA » pour Streamlit : appelle POST /api/chat de l'API."""
import html
import os
import time

import requests
import streamlit as st

try:  # réutilise l'adresse de l'API déjà configurée dans api_client.py
    import api_client
    API_URL = getattr(api_client, "API_URL", None) or os.getenv("API_URL", "http://localhost:8000")
except ImportError:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
API_URL = str(API_URL).rstrip("/")

BLUE, ACCENT = "#1E3A8A", "#2563EB"
SUGGESTIONS = [
    "Quels stages en Data à Casablanca ?",
    "Offres de télétravail",
    "Quelles compétences sont les plus demandées ?",
    "Comment adapter mon CV à une offre ?",
]

CSS = f"""
<style>
.chat-hero {{background:{BLUE}; color:#fff; border-radius:16px; padding:1.4rem 1.6rem; margin-bottom:1rem;}}
.chat-hero h2 {{margin:0 0 .25rem 0; color:#fff; font-size:1.6rem;}}
.chat-hero p {{margin:0; color:#BFDBFE; font-size:.98rem;}}
[data-testid="stChatMessage"] {{border-radius:14px; padding:.8rem 1rem; margin-bottom:.4rem; background:#F1F5F9;}}
.offer-card {{background:#fff; border:1px solid #CBD5E1; border-radius:12px; padding:.75rem .95rem; margin:.45rem 0;}}
.offer-card .t {{font-weight:700; color:{BLUE}; font-size:1rem;}}
.offer-card .m {{color:#475569; font-size:.9rem; margin:.15rem 0 .4rem 0;}}
.badge {{display:inline-block; background:#DBEAFE; color:{BLUE}; border-radius:999px; padding:.1rem .6rem;
        font-size:.78rem; margin-right:.35rem;}}
.badge.s {{background:{ACCENT}; color:#fff;}}
.offer-card a {{color:{ACCENT}; font-size:.88rem; text-decoration:none; font-weight:600;}}
</style>
"""


def _offer_card(o):
    esc = lambda v: html.escape(str(v))
    meta = " · ".join(esc(o[k]) for k in ("company", "city") if o.get(k))
    badges = ""
    if o.get("contract"):
        badges += f'<span class="badge">{esc(o["contract"])}</span>'
    if o.get("domain"):
        badges += f'<span class="badge">{esc(o["domain"])}</span>'
    if o.get("salary_mad"):
        badges += f'<span class="badge s">{o["salary_mad"]:,} MAD</span>'.replace(",", " ")
    else:
        badges += '<span class="badge">Rémunération non renseignée</span>'
    link = ""
    url = o.get("url") or ""
    if url.startswith("http"):
        link = f'<br><a href="{html.escape(url)}" target="_blank" rel="noopener">Voir l\'offre →</a>'
    return (f'<div class="offer-card"><div class="t">{esc(o.get("title", ""))}</div>'
            f'<div class="m">{meta}</div>{badges}{link}</div>')


def _show(msg):
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        for o in msg.get("offers", []):
            st.markdown(_offer_card(o), unsafe_allow_html=True)


def _ask(history):
    payload = [{"role": m["role"], "content": m["content"]} for m in history]
    for attempt in range(2):  # l'API gratuite de Render peut mettre ~1 min à se réveiller
        try:
            r = requests.post(f"{API_URL}/api/chat", json={"messages": payload}, timeout=90)
            if r.ok:
                d = r.json()
                return d.get("answer", ""), d.get("offers", [])
            detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
            return f"⚠️ Erreur {r.status_code} : {detail}", []
        except requests.RequestException:
            if attempt == 0:
                time.sleep(5)
    return "⚠️ L'assistant ne répond pas pour le moment. Réessaie dans quelques secondes.", []


def render_chatbot():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="chat-hero"><h2>🤖 Assistant IA</h2>'
                '<p>Trouve des offres, compare-les et prépare ta candidature en discutant.</p></div>',
                unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state.chat = []

    prompt = st.chat_input("Écris ta question…")
    if not prompt and st.session_state.get("pending"):
        prompt = st.session_state.pop("pending")

    if not st.session_state.chat and not prompt:
        _show({"role": "assistant", "content":
               "Bonjour ! 👋 Je peux t'aider à **trouver une offre**, comprendre le marché "
               "ou **améliorer ton CV**. Choisis une idée ou écris ta question :"})
        cols = st.columns(2)
        for i, s in enumerate(SUGGESTIONS):
            if cols[i % 2].button(s, key=f"sugg{i}", use_container_width=True):
                st.session_state.pending = s
                st.rerun()
    else:
        for m in st.session_state.chat:
            _show(m)

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        _show(st.session_state.chat[-1])
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Je cherche dans les offres…"):
                answer, offers = _ask(st.session_state.chat)
        reply = {"role": "assistant", "content": answer, "offers": offers}
        st.session_state.chat.append(reply)
        _show(reply)

    if st.session_state.chat:
        if st.button("🗑️ Nouvelle conversation"):
            st.session_state.chat = []
            st.rerun()
