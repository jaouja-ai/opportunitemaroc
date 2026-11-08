"""Logique métier : chargement, filtres, statistiques et insights."""
import json

import pandas as pd

from .data_processing import MISSING, clean_offers
from .database import read_offers_df


def get_clean_df() -> pd.DataFrame:
    return clean_offers(read_offers_df())


def apply_filters(df, q=None, city=None, contract=None, domain=None, level=None, kind=None,
                  remote=False, only_salary=False, min_salary=None, days=None) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if q:  # chaque mot doit apparaître dans titre / entreprise / compétences / domaine
        hay = (df["title"] + " " + df["company"] + " " + df["skills"] + " " + df["domain"]).str.lower()
        for term in q.lower().split():
            mask &= hay.str.contains(term, regex=False)
    for col, values in (("city", city), ("contract", contract), ("domain", domain), ("level", level)):
        if values:
            mask &= df[col].isin(values)
    if kind and kind != "Tous":
        mask &= df["kind"] == kind
    if remote:
        mask &= df["remote"]
    if only_salary:
        mask &= df["salary_known"]
    if min_salary:  # les offres sans salaire connu sont exclues quand un minimum est demandé
        mask &= df["salary_mad"].fillna(-1) >= min_salary
    if days:
        mask &= df["posted_date"] >= pd.Timestamp.today().normalize() - pd.Timedelta(days=days)
    return df[mask].sort_values("posted_date", ascending=False)


def to_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    for col in ("posted_date", "deadline", "collected_date"):
        out[col] = out[col].dt.strftime("%Y-%m-%d")  # NaT -> null
    return json.loads(out.to_json(orient="records"))


def _share(count, total) -> int:
    return round(100 * count / total) if total else 0


def compute_stats(df: pd.DataFrame) -> dict:
    n = len(df)
    if n == 0:
        return {"total": 0, "cities": 0, "companies": 0, "salary_share": 0, "median_salary": None,
                "insights": ["Aucune offre ne correspond à ces filtres."]}
    known = lambda col: df[df[col] != MISSING][col]  # noqa: E731
    cities, domains = known("city").value_counts(), known("domain").value_counts()
    companies, salaries = known("company").value_counts(), df.loc[df["salary_known"], "salary_mad"]
    insights = []
    if len(cities):
        insights.append(f"{cities.index[0]} concentre {_share(cities.iloc[0], n)} % des offres, devant {cities.index[1]}." if len(cities) > 1
                        else f"Toutes les offres sont à {cities.index[0]}.")
    if len(domains):
        insights.append(f"Le domaine le plus recruteur est « {domains.index[0]} » ({_share(domains.iloc[0], n)} % des offres).")
    if len(companies):
        insights.append(f"{companies.index[0]} publie le plus d'offres ({companies.iloc[0]}).")
    if len(salaries):
        insights.append(f"Seules {_share(len(salaries), n)} % des offres indiquent une rémunération ; médiane : {int(salaries.median()):,} MAD.".replace(",", " "))
    stage = df[df["kind"] == "Stage"]
    if len(stage):
        insights.append(f"{_share((stage['contract'] == 'PFE').sum(), len(stage))} % des stages sont des PFE.")
    insights.append(f"{_share(df['date_imputed'].sum(), n)} % des dates de publication sont estimées (date de collecte).")
    return {"total": n, "cities": int(df["city"].nunique()), "companies": int(df["company"].nunique()),
            "salary_share": _share(len(salaries), n),
            "median_salary": int(salaries.median()) if len(salaries) else None, "insights": insights}
