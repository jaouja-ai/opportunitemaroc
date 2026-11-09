"""Chatbot OpportuniteMaroc : route POST /api/chat.

Utilise n'importe quelle API compatible OpenAI (Groq, Gemini, OpenRouter...) via les
variables LLM_API_KEY, LLM_BASE_URL et LLM_MODEL : aucune nouvelle dépendance.
La réponse contient le texte de l'assistant ET les offres de la base les plus
pertinentes, que l'interface affiche sous forme de cartes.
"""
import os

import pandas as pd
from fastapi import APIRouter, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from backend.database import read_offers_df

router = APIRouter(prefix="/api", tags=["chatbot"])

SYSTEM = (
    "Tu es l'assistant d'OpportuniteMaroc, une plateforme d'offres de stage et d'emploi "
    "digital pour les étudiants marocains. Réponds en français, de façon courte, claire et "
    "chaleureuse (4 à 6 lignes maximum, listes à puces si utile). "
    "Appuie-toi UNIQUEMENT sur les offres fournies ci-dessous pour parler des offres : "
    "n'invente jamais une offre, un salaire ou une entreprise. S'il n'y a pas d'offre "
    "correspondante, dis-le et propose de modifier les critères (ville, domaine, contrat). "
    "Quand tu cites une offre, donne son titre, l'entreprise et la ville. "
    "Tu peux aussi donner des conseils sur le CV, la lettre de motivation et les entretiens. "
    "Si la question n'a aucun rapport avec les stages, l'emploi ou la carrière, ramène "
    "poliment la conversation vers ces sujets. "
    "Les offres de la plateforme sont en grande partie des données de démonstration : "
    "mentionne-le une fois si on te demande de postuler."
)

COLS = ["title", "company", "city", "kind", "contract", "domain", "level", "salary_mad", "skills"]


class Msg(BaseModel):
    role: str  # "user" ou "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Msg]


def _clean(v):
    return None if v is None or (isinstance(v, float) and pd.isna(v)) or str(v) in ("", "nan", "None") else v


def _search(question: str, n: int = 25):
    """Retourne (texte de contexte, liste d'offres pertinentes pour les cartes)."""
    try:
        df = read_offers_df()
    except Exception:
        return "Aucune offre disponible.", []
    if df.empty:
        return "Aucune offre disponible.", []

    cols = [c for c in COLS if c in df.columns]
    words = [w.strip("?!.,;:'\"") for w in question.lower().split()]
    words = [w for w in words if len(w) > 2]
    text = df[cols].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    score = text.apply(lambda t: sum(w in t for w in words))
    ranked = df.assign(_score=score).sort_values("_score", ascending=False)

    lines = []
    for _, row in ranked.head(n).iterrows():
        parts = [f"{c}: {row[c]}" for c in cols if _clean(row[c]) is not None]
        lines.append(" | ".join(parts))

    cards = []
    for _, row in ranked[ranked["_score"] > 0].head(3).iterrows():
        sal = _clean(row.get("salary_mad"))
        cards.append({
            "title": str(_clean(row.get("title")) or ""),
            "company": _clean(row.get("company")),
            "city": _clean(row.get("city")),
            "contract": _clean(row.get("contract")),
            "domain": _clean(row.get("domain")),
            "salary_mad": int(float(sal)) if sal is not None else None,
            "url": _clean(row.get("url")),
        })
    return "\n".join(lines), cards


@router.post("/chat")
def chat(req: ChatRequest):
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise HTTPException(503, "Chatbot non configuré : LLM_API_KEY manquante.")

    msgs = [m.model_dump() for m in req.messages[-12:]
            if m.role in ("user", "assistant") and m.content.strip()]
    while msgs and msgs[0]["role"] != "user":  # l'API exige de commencer par l'utilisateur
        msgs.pop(0)
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(400, "Message utilisateur manquant.")

    context, offers = _search(msgs[-1]["content"])
    system = SYSTEM + "\n\nOFFRES PERTINENTES :\n" + context
    client = OpenAI(
        api_key=key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        timeout=45,
    )
    try:
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            max_tokens=600,
            messages=[{"role": "system", "content": system}] + msgs,
        )
    except OpenAIError as e:
        raise HTTPException(502, f"Erreur du modèle : {e}")
    return {"answer": resp.choices[0].message.content or "", "offers": offers}
