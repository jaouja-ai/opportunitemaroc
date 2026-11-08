"""Accès base de données : SQLite par défaut, PostgreSQL en changeant DATABASE_URL."""
import pandas as pd
from sqlalchemy import (Boolean, Column, Date, Integer, MetaData, String, Table, Text,
                        create_engine, delete, func, insert, select)

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
    Column("is_demo", Boolean, default=True),
)


def init_db():
    metadata.create_all(engine)  # crée les tables si absentes


def count_offers() -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(offers)).scalar_one()


def insert_offers(rows: list[dict]):
    with engine.begin() as conn:
        conn.execute(insert(offers), rows)


def reset_offers():
    """Supprime uniquement les offres de démonstration (les vraies offres sont conservées)."""
    with engine.begin() as conn:
        conn.execute(delete(offers).where(offers.c.is_demo.is_(True)))


def read_offers_df() -> pd.DataFrame:
    init_db()  # idempotent : garantit que la table existe, même avant le premier démarrage de l'API
    with engine.connect() as conn:
        return pd.read_sql(select(offers), conn)
