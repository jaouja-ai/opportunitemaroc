"""API FastAPI (offres, filtres, stats, CV) + dashboard Dash monté sur /dashboard."""
from contextlib import asynccontextmanager
from typing import Optional

from a2wsgi import WSGIMiddleware
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field

from dashboard.app import create_dash_app

from .ai_cv import adapt_cv
from .data_processing import MISSING, missing_report
from .database import read_offers_df
from .pdf_cv import build_pdf
from .seed import seed_if_empty
from .services import apply_filters, compute_stats, get_clean_df, to_records


@asynccontextmanager
async def lifespan(_):
    seed_if_empty()  # base vide -> données de démonstration
    yield


app = FastAPI(title="OPPORTUNITEMAROC API", version="1.0", lifespan=lifespan)


class OfferFilters:
    """Paramètres de requête communs (listes répétables : ?city=Rabat&city=Fès)."""

    def __init__(self, q: Optional[str] = None, city: list[str] = Query(default=[]), contract: list[str] = Query(default=[]),
                 domain: list[str] = Query(default=[]), level: list[str] = Query(default=[]), kind: Optional[str] = None,
                 remote: bool = False, only_salary: bool = False, min_salary: Optional[int] = None, days: Optional[int] = None):
        self.q, self.city, self.contract, self.domain, self.level = q, city, contract, domain, level
        self.kind, self.remote, self.only_salary, self.min_salary, self.days = kind, remote, only_salary, min_salary, days


class Experience(BaseModel):
    role: str = ""
    company: str = ""
    period: str = ""
    description: str = ""


class Education(BaseModel):
    degree: str = ""
    school: str = ""
    period: str = ""


class Profile(BaseModel):
    full_name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class CVDoc(Profile):
    target: str = ""
    keywords: list[str] = Field(default_factory=list)
    mode: str = "règles"


class GenerateRequest(BaseModel):
    profile: Profile
    offer_id: Optional[int] = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/filters")
def filters():
    df = get_clean_df()
    options = lambda col: sorted(v for v in df[col].unique() if v != MISSING)  # noqa: E731
    return {"cities": options("city"), "contracts": options("contract"), "domains": options("domain"),
            "levels": options("level"), "kinds": ["Stage", "Emploi"]}


@app.get("/api/offers")
def list_offers(f: OfferFilters = Depends(), limit: int = Query(20, ge=1, le=500), offset: int = Query(0, ge=0)):
    df = apply_filters(get_clean_df(), **vars(f))
    return {"total": len(df), "items": to_records(df.iloc[offset:offset + limit])}


@app.get("/api/offers/{offer_id}")
def get_offer(offer_id: int):
    df = get_clean_df()
    row = df[df["id"] == offer_id]
    if row.empty:
        raise HTTPException(404, "Offre introuvable")
    return to_records(row)[0]


@app.get("/api/stats")
def stats():
    raw = read_offers_df()
    return {**compute_stats(get_clean_df()), "missing": missing_report(raw).to_dict("records"),
            "demo": bool(len(raw)) and bool(raw["is_demo"].any())}


@app.post("/api/cv/generate")
def generate_cv(req: GenerateRequest):
    offer = None
    if req.offer_id is not None:
        rows = get_clean_df().query("id == @req.offer_id")
        if rows.empty:
            raise HTTPException(404, "Offre introuvable")
        offer = to_records(rows)[0]
    return adapt_cv(req.profile.model_dump(), offer)


@app.post("/api/cv/pdf")
def cv_pdf(cv: CVDoc):
    return Response(build_pdf(cv.model_dump()), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="cv.pdf"'})


app.mount("/dashboard", WSGIMiddleware(create_dash_app().server))  # Dash servi par la même API
