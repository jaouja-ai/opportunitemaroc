"""Adaptation du CV à une offre : IA (API compatible OpenAI) avec repli par règles si pas de clé."""
import json
import re

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM = (
    "Tu es un expert en recrutement au Maroc. Adapte le CV à l'offre SANS JAMAIS inventer d'expérience, "
    "de diplôme ou de compétence absents du profil : tu reformules et tu réordonnes uniquement. "
    "Réponds UNIQUEMENT en JSON avec les clés : summary (3 phrases max), skills (liste ordonnée, tirée du profil), "
    "experiences (mêmes expériences reformulées : role, company, period, description), "
    "keywords (mots-clés de l'offre présents dans le profil)."
)


def _split(text: str) -> list[str]:
    return [s.strip() for s in (text or "").split(",") if s.strip()]


def rule_based(profile: dict, offer: dict | None) -> dict:
    """Repli sans IA : met en avant les compétences communes avec l'offre."""
    skills = profile.get("skills", [])
    wanted = {s.lower() for s in _split(offer.get("skills", ""))} if offer else set()
    matched = [s for s in skills if s.lower() in wanted]
    ordered = matched + [s for s in skills if s not in matched]
    summary = profile.get("summary", "").strip()
    if offer:
        pitch = f"Candidat(e) motivé(e) par le poste « {offer['title']} » chez {offer['company']}"
        pitch += f", avec une expertise en {', '.join(matched[:4])}." if matched else "."
        summary = f"{summary} {pitch}".strip()
    return {**profile, "summary": summary, "skills": ordered, "keywords": matched, "mode": "règles",
            "target": f"{offer['title']} — {offer['company']}" if offer else ""}


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group(0))


def adapt_cv(profile: dict, offer: dict | None) -> dict:
    result = rule_based(profile, offer)
    if not LLM_API_KEY:
        return result
    try:
        from openai import OpenAI
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        user = json.dumps({"profil": profile, "offre": offer}, ensure_ascii=False, default=str)
        resp = client.chat.completions.create(
            model=LLM_MODEL, temperature=0.3,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
        data = _parse_json(resp.choices[0].message.content)
        own = {s.lower(): s for s in profile.get("skills", [])}
        result["skills"] = [own[s.lower()] for s in data.get("skills", []) if s.lower() in own] or result["skills"]  # anti-invention
        result["summary"] = str(data.get("summary") or result["summary"])
        result["keywords"] = [str(k) for k in data.get("keywords", [])] or result["keywords"]
        exps = data.get("experiences", [])
        if len(exps) == len(profile.get("experiences", [])):  # on garde les expériences d'origine si le compte diffère
            result["experiences"] = [{k: str(e.get(k, "")) for k in ("role", "company", "period", "description")} for e in exps]
        result["mode"] = "IA"
    except Exception as exc:  # réseau, clé invalide, JSON illisible... -> on garde le repli
        result["mode"] = f"règles (IA indisponible : {type(exc).__name__})"
    return result
