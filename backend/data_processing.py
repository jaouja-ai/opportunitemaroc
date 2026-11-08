"""Nettoyage des offres et gestion explicite des valeurs manquantes.

Stratégie, colonne par colonne :
- title            : manquant -> LIGNE SUPPRIMÉE (une offre sans titre est inexploitable)
- company, city, domain, level, contract, source : manquant -> "Non renseigné" (affiché en gris dans les graphiques)
- posted_date      : manquant -> remplacée par la date de collecte (colonne date_imputed = True)
- deadline         : manquant -> conservée vide (NaT), jamais inventée
- salary_mad       : manquant -> conservée vide ; colonne salary_known ; la médiane n'utilise que les valeurs connues
- skills           : manquant -> chaîne vide ; remote : manquant -> False
"""
import numpy as np
import pandas as pd

MISSING = "Non renseigné"
CAT_COLS = ["company", "city", "domain", "level", "contract", "source"]


def _blank_to_nan(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(r"^\s*$", np.nan, regex=True)  # chaînes vides = manquantes


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Nombre et pourcentage de valeurs manquantes par colonne (sur les données brutes)."""
    df = _blank_to_nan(df)
    rep = pd.DataFrame({"colonne": df.columns, "manquants": df.isna().sum().to_numpy()})
    rep["pourcentage"] = (rep["manquants"] / max(len(df), 1) * 100).round(1)
    return rep.sort_values("pourcentage", ascending=False).reset_index(drop=True)


def clean_offers(df: pd.DataFrame) -> pd.DataFrame:
    df = _blank_to_nan(df.copy())
    df = df.dropna(subset=["title"])                      # suppression contrôlée
    for col in CAT_COLS:
        df[col] = df[col].fillna(MISSING).astype(str).str.strip()
    df["collected_date"] = pd.to_datetime(df["collected_date"], errors="coerce")
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    df["date_imputed"] = df["posted_date"].isna()          # trace de l'imputation
    df["posted_date"] = df["posted_date"].fillna(df["collected_date"])
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    df["salary_mad"] = pd.to_numeric(df["salary_mad"], errors="coerce")
    df["salary_known"] = df["salary_mad"].notna()
    df["remote"] = df["remote"].fillna(False).astype(bool)
    df["skills"] = df["skills"].fillna("").astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    default_kind = df["contract"].isin(["CDI", "CDD"]).map({True: "Emploi", False: "Stage"})
    df["kind"] = df["kind"].fillna(default_kind)
    return df.reset_index(drop=True)
