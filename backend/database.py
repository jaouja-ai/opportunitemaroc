"""Accès base de données : SQLite par défaut, PostgreSQL en changeant DATABASE_URL."""
from urllib.parse import urlsplit

import numpy as np
import pandas as pd
from sqlalchemy import (Boolean, Column, Date, Integer, MetaData, String, Table, Text,
                        create_engine, delete, insert, select)

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

offers = Table(
    "offers", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(200), nullable=False),
    Column("company", String(150)),
    Column("city", String(80)),
    Column("kind", String(20)),          # Stage / Emploi
    Column("contract", String(40)),      # PFE, Stage d'été, Pré-embauche, ...
    Column("domain", String(80)),
    Column("level", String(30)),
    Column("salary_mad", Integer),       # NULL = non renseigné
    Column("remote", Boolean, default=False),
    Column("skills", Text),              # compétences séparées par des virgules
    Column("description", Text),
    Column("source", String(80)),
    Column("url", String(300)),
    Column("posted_date", Date),
    Column("deadline", Date),
    Column("collected_date", Date),
    Column("is_demo", Boolean, nullable=False, default=False),
)


def is_valid_offer_url(value) -> bool:
    """Accept absolute HTTP(S) offer URLs, but reject known placeholder domains."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value.strip())
        host = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"} or not host:
        return False
    host = host.lower().rstrip(".")
    if any(char.isspace() for char in host):
        return False
    if host in {"example.com", "example.org", "example.net"} or any(
            host.endswith(f".{domain}") for domain in ("example.com", "example.org", "example.net")):
        return False
    return not (host.endswith(".invalid") or host.endswith(".test"))


def init_db():
    metadata.create_all(engine)
    with engine.begin() as conn:
        rows = conn.execute(select(offers.c.id, offers.c.url, offers.c.is_demo)).all()
        invalid_ids = [
            row.id for row in rows
            if row.is_demo is not False or not is_valid_offer_url(row.url)
        ]
        if invalid_ids:
            conn.execute(delete(offers).where(offers.c.id.in_(invalid_ids)))


def insert_offers(rows: list[dict]):
    for row in rows:
        is_demo = row.get("is_demo")
        if not isinstance(is_demo, (bool, np.bool_)) or bool(is_demo):
            raise ValueError("Only offers explicitly marked is_demo=False can be saved.")
        if not is_valid_offer_url(row.get("url")):
            raise ValueError(f"Offer has no valid non-placeholder HTTP(S) URL: {row.get('title', '')}")
    with engine.begin() as conn:
        if rows:
            conn.execute(insert(offers), rows)


def reset_offers():
    """Supprime uniquement les offres de démonstration (les vraies offres sont conservées)."""
    with engine.begin() as conn:
        conn.execute(delete(offers).where(offers.c.is_demo.is_(True)))


def read_offers_df() -> pd.DataFrame:
    init_db()
    with engine.connect() as conn:
        df = pd.read_sql(select(offers).where(offers.c.is_demo.is_(False)), conn)
    if df.empty:
        return df
    return df[df["url"].map(is_valid_offer_url)].reset_index(drop=True)
