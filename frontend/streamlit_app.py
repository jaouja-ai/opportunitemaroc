"""Interface Streamlit : Offres (filtres intégrés), Générateur de CV, Statistiques & Insights."""
import html
import math
import time

import pandas as pd
import streamlit as st

import api_client as api
from styles import CSS

try:
    from chatbot_ui import render_chatbot  # fichier voisin, comme api_client
except ImportError:
    from frontend.chatbot_ui import render_chatbot

st.set_page_config(page_title="OPPORTUNITEMAROC", page_icon="🎓", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

PAGES = ["Offres", "Générateur de CV", "Statistiques & Insights", "Assistant IA"]
NA = "Non renseigné"
esc = lambda v: html.escape(str(v if v is not None else ""))  # noqa: E731

def hero(title, subtitle, demo=False):
    badge = "<div class='demo'>Contient des données de démonstration (extraites)</div>" if demo else ""
    st.markdown(f"<div class='hero'><h1>{esc(title)}</h1><p>{esc(subtitle)}</p>{badge}</div>", unsafe_allow_html=True)

def select_offer(offer_id):  # bouton « Adapter mon CV » : mémorise l'offre et ouvre le générateur
    st.session_state.selected_offer = offer_id
    st.session_state.nav = PAGES[1]


def badge(text, cls=""):
    return f"<span class='badge {'na' if text == NA else cls}'>{esc(text)}</span>"


def offer_card(o):
    salary = f"{int(o['salary_mad']):,} MAD / mois".replace(",", " ") if o.get("salary_mad") else None
    badges = badge(o["contract"]) + badge(o["city"]) + badge(o["domain"]) + badge(o["level"])
    badges += badge("Télétravail possible") if o.get("remote") else ""
    badges += badge(salary, "pay") if salary else badge("Rémunération non renseignée", "na")
    with st.container(border=True):
        st.markdown(f"<div class='offer-title'>{esc(o['title'])}</div><div class='offer-meta'>{esc(o['company'])}"
                    f" · publiée le {esc((o.get('posted_date') or '')[:10])}</div>{badges}", unsafe_allow_html=True)
        left, right = st.columns([1, 3])
        left.button("Adapter mon CV", key=f"cv_{o['id']}", on_click=select_offer, args=(o["id"],), type="primary")
        with right.expander("Détails de l'offre"):
            st.write(o.get("description") or "Description non renseignée.")
            st.markdown("**Compétences :** " + (esc(o.get("skills")) or "_non renseignées_"))
            st.markdown(f"**Date limite :** {o.get('deadline') or '_non renseignée_'} · **Source :** {esc(o['source'])}")
            st.markdown(f"[Voir l'offre]({esc(o.get('url'))})")


def page_offers():
    stats, opts = api.get_stats(), api.get_filters()
    hero("Trouvez votre stage ou emploi digital au Maroc", "Recherchez, filtrez et adaptez votre CV en un clic.", stats["demo"])
    with st.sidebar:
        st.markdown("### Filtres")
        q = st.text_input("Recherche", placeholder="Titre, entreprise, compétence…")
        kind = st.radio("Type", ["Tous", "Stage", "Emploi"], horizontal=True)
        contract = st.multiselect("Contrat", opts["contracts"])
        city = st.multiselect("Ville", opts["cities"])
        domain = st.multiselect("Domaine", opts["domains"])
        level = st.multiselect("Niveau", opts["levels"])
        remote = st.checkbox("Télétravail possible")
        only_salary = st.checkbox("Rémunération indiquée uniquement")
        days = st.select_slider("Publiée depuis", options=[7, 14, 30, 60, 90, 9999], value=9999,
                                format_func=lambda d: "Toutes les dates" if d == 9999 else f"{d} jours")
    params = {"q": q, "kind": kind, "city": city, "contract": contract, "domain": domain, "level": level,
              "limit": 500, "days": None if days == 9999 else days,
              "remote": "true" if remote else None, "only_salary": "true" if only_salary else None}
    res = api.get_offers({k: v for k, v in params.items() if v not in (None, "", [])})
    items = res["items"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Offres trouvées", res["total"])
    c2.metric("Villes", len({o["city"] for o in items if o["city"] != NA}))
    c3.metric("Entreprises", len({o["company"] for o in items if o["company"] != NA}))
    if not items:
        st.info("Aucune offre ne correspond à ces filtres. Essayez d'en retirer quelques-uns.")
        return
    per_page, pages = 10, max(1, math.ceil(len(items) / 10))
    page = st.number_input("Page", 1, pages, 1) if pages > 1 else 1
    for o in items[(page - 1) * per_page: page * per_page]:
        offer_card(o)


def page_cv():
    hero("Générateur de CV", "Adaptez votre CV à une offre, puis téléchargez-le en PDF.")
    res = api.get_offers({"limit": 500})
    labels = {o["id"]: f"{o['title']} — {o['company']} ({o['city']})" for o in res["items"]}
    ids = [None] + list(labels)
    current = st.session_state.get("selected_offer")
    offer_id = st.selectbox("Offre ciblée", ids, index=ids.index(current) if current in ids else 0,
                            format_func=lambda i: "Aucune (CV générique)" if i is None else labels[i])
    st.caption("Exemple de profil à remplacer par le vôtre. L'IA reformule sans jamais inventer d'expérience.")
    a, b = st.columns(2)
    full_name, title = a.text_input("Nom complet", "Prénom NOM"), b.text_input("Titre", "Étudiant(e) en Data & IA")
    email, phone = a.text_input("Email", "prenom.nom@email.com"), b.text_input("Téléphone", "+212 6 00 00 00 00")
    city = a.text_input("Ville", "Marrakech")
    languages = b.text_input("Langues (séparées par des virgules)", "Arabe, Français, Anglais")
    summary = st.text_area("Résumé", "Étudiant(e) motivé(e), curieux(se) et rigoureux(se), à la recherche d'un stage.")
    skills = st.text_input("Compétences (séparées par des virgules)", "Python, SQL, Pandas, Power BI, Excel")
    st.markdown("**Expériences** (ajoutez des lignes avec le + du tableau)")
    exp = st.data_editor(pd.DataFrame([{"role": "Projet académique", "company": "Université", "period": "2025",
                                        "description": "Analyse de données d'offres de stage\nVisualisation avec Matplotlib"}]),
                         num_rows="dynamic", width="stretch", key="exp")
    st.markdown("**Formation**")
    edu = st.data_editor(pd.DataFrame([{"degree": "Licence / Master", "school": "Établissement", "period": "2023 - 2026"}]),
                         num_rows="dynamic", width="stretch", key="edu")
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
    if st.button("Adapter mon CV", type="primary"):
        payload = {"offer_id": offer_id, "profile": {
            "full_name": full_name, "title": title, "email": email, "phone": phone, "city": city, "summary": summary,
            "skills": split(skills), "languages": split(languages),
            "experiences": exp.fillna("").to_dict("records"), "education": edu.fillna("").to_dict("records")}}
        with st.spinner("Adaptation en cours…"):
            st.session_state.cv = api.generate_cv(payload)
    cv = st.session_state.get("cv")
    if cv:
        st.success(f"CV adapté — mode : {cv['mode']}" + (f" · cible : {cv['target']}" if cv.get("target") else ""))
        if cv["mode"].startswith("règles"):
            st.caption("Pour activer l'IA, renseignez LLM_API_KEY dans le fichier .env (voir README).")
        cv["summary"] = st.text_area("Résumé adapté (modifiable)", cv["summary"], key=f"sum_{hash(cv['summary'])}")
        st.markdown("**Compétences (mises en avant en premier)**")
        st.markdown("".join(f"<span class='chip {'kw' if s in cv['keywords'] else ''}'>{esc(s)}</span>" for s in cv["skills"]),
                    unsafe_allow_html=True)
        if cv["keywords"]:
            st.caption("En bleu clair : compétences qui correspondent aux mots-clés de l'offre.")
        st.download_button("Télécharger le CV (PDF)", api.cv_pdf(cv), file_name="cv.pdf", mime="application/pdf")


def page_stats():
    stats = api.get_stats()
    hero("Statistiques & Insights", "Comprenez le marché en quelques secondes.", stats["demo"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Offres", stats["total"])
    c2.metric("Villes", stats["cities"])
    c3.metric("Entreprises", stats["companies"])
    c4.metric("Avec rémunération", f"{stats['salary_share']} %")
    st.markdown("### Insights clés")
    st.markdown("".join(f"<div class='insight'>{esc(t)}</div>" for t in stats["insights"]), unsafe_allow_html=True)
    with st.expander("Comment sont traitées les valeurs manquantes ?"):
        st.markdown(
            "- **Titre manquant** : offre supprimée (inexploitable)\n"
            "- **Ville, domaine, niveau, entreprise** : « Non renseigné », affiché **en gris** dans les graphiques\n"
            "- **Date de publication** : remplacée par la date de collecte (signalée dans le graphique temporel)\n"
            "- **Rémunération, date limite** : laissées vides, jamais inventées ; la médiane n'utilise que les valeurs connues")
        st.dataframe(pd.DataFrame(stats["missing"]), width="stretch", hide_index=True)
    st.markdown("### Visualisations interactives")
    st.iframe(f"{api.PUBLIC_API_URL}/dashboard/", height=1650)  # Dash servi par l'API (URL publique)


def page_chat():
    render_chatbot()


def wait_for_api(tries=6, delay=10):
    """L'API gratuite (Render) peut dormir : on attend son réveil au lieu d'afficher une erreur."""
    for _ in range(tries):
        if api.api_ok():
            return True
        time.sleep(delay)
    return False


# --- navigation ---
if "nav" not in st.session_state:
    st.session_state.nav = PAGES[0]
st.sidebar.markdown("<div class='brand'>OPPORTUNITE<b>MAROC</b></div>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", PAGES, key="nav", label_visibility="collapsed")
if not api.api_ok():
    with st.spinner("Réveil du serveur en cours (jusqu'à 1 minute)…"):
        ready = wait_for_api()
    if not ready:
        st.error("L'API ne répond pas pour le moment. Recharge la page dans un instant "
                 "(en local : lancez l'application avec `python run.py`).")
        st.stop()
{PAGES[0]: page_offers, PAGES[1]: page_cv, PAGES[2]: page_stats, PAGES[3]: page_chat}[page]()
