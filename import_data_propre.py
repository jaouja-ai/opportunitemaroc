from datetime import date, datetime
from pathlib import Path
import re
import shutil
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data_propre.csv"
DB_PATH = BASE_DIR / "opportunitemaroc.db"
TABLE_NAME = "offers"

SOURCE_URLS = {
    "linkedin": "https://www.linkedin.com/jobs/",
    "stagiaires.ma": "https://www.stagiaires.ma/",
    "rekrute.com": "https://www.rekrute.com/",
}
DEFAULT_URL = "https://www.linkedin.com/jobs/"


def fix_cp1252(val):
    if not isinstance(val, str):
        return val
    try:
        return val.encode("latin1").decode("cp1252")
    except Exception:
        return val


def clean_str(val) -> str | None:
    if pd.isna(val):
        return None
    s = fix_cp1252(str(val)).strip()
    if not s or s.lower() in {"nan", "none", "null", "non précisé", "non precise", "n/a", "-"}:
        return None
    return s


def parse_salary_mad(val) -> float | None:
    s = clean_str(val)
    if not s:
        return None
    match = re.search(r"(\d[\d\s.,]*)", s.replace("\u00a0", " "))
    if not match:
        return None
    num_str = match.group(1).replace(" ", "").replace(",", ".")
    if re.fullmatch(r"\d+\.\d{3}", num_str):
        num_str = num_str.replace(".", "")
    try:
        return float(num_str)
    except ValueError:
        return None


def build_description(row: pd.Series) -> str:
    parts = []
    desc = clean_str(row.get("description"))
    duree = clean_str(row.get("duree"))
    remun = clean_str(row.get("remuneration"))

    if desc:
        parts.append(desc)
    if duree:
        parts.append(f"Durée : {duree}")
    if remun:
        parts.append(f"Rémunération : {remun}")

    return "\n".join(parts) if parts else "Non précisé"


def build_source_url(source: str | None) -> str:
    if not source:
        return DEFAULT_URL
    key = source.strip().lower()
    for k, url in SOURCE_URLS.items():
        if k in key:
            return url
    return DEFAULT_URL


def backup_database(db_path: Path) -> Path | None:
    if not db_path.exists():
        print(f"Base introuvable : {db_path}")
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}_backup_{stamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    print(f"Sauvegarde créée : {backup_path.name}")
    return backup_path


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {CSV_PATH}")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base introuvable : {DB_PATH}")

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"Lignes lues dans data_propre.csv : {len(df)}")

    backup_database(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        db_cols = [row[1] for row in cursor.execute(f"PRAGMA table_info({TABLE_NAME});").fetchall()]
        existing_keys = set(
            cursor.execute(
                f"SELECT LOWER(TRIM(COALESCE(title, ''))), LOWER(TRIM(COALESCE(company, ''))), COALESCE(posted_date, '') FROM {TABLE_NAME}"
            ).fetchall()
        )

        today_str = date.today().isoformat()
        rows_to_insert = []
        skipped_duplicates = 0

        for _, row in df.iterrows():
            title = clean_str(row.get("titre_offre"))
            if not title:
                continue

            company = clean_str(row.get("entreprise")) or "Non précisé"
            city = clean_str(row.get("ville")) or "Marrakech"
            posted_date = clean_str(row.get("date_publication")) or today_str
            source = clean_str(row.get("plateforme_source")) or "LinkedIn"
            domain = clean_str(row.get("domaine"))
            contract = clean_str(row.get("type_contrat"))
            description = build_description(row)
            salary_mad = parse_salary_mad(row.get("remuneration"))
            url = build_source_url(source)

            text_for_kind = f"{title} {contract or ''} {description or ''}".lower()
            kind = "Stage" if any(k in text_for_kind for k in ["stage", "pfe", "stage/pfe"]) else "Emploi"

            dedup_key = (title.lower(), company.lower(), posted_date)
            if dedup_key in existing_keys:
                skipped_duplicates += 1
                continue
            existing_keys.add(dedup_key)

            record = {
                "title": title,
                "company": company,
                "city": city,
                "kind": kind,
                "contract": contract,
                "domain": domain,
                "level": None,
                "salary_mad": salary_mad,
                "remote": 0,
                "skills": None,
                "description": description,
                "source": source,
                "url": url,
                "posted_date": posted_date,
                "deadline": None,
                "collected_date": today_str,
                "is_demo": 0,
            }

            filtered_record = {k: v for k, v in record.items() if k in db_cols and k != "id"}
            rows_to_insert.append(filtered_record)

        if rows_to_insert:
            cols = list(rows_to_insert[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            sql = f"INSERT INTO {TABLE_NAME} ({col_names}) VALUES ({placeholders})"
            cursor.executemany(sql, [[r[c] for c in cols] for r in rows_to_insert])
            conn.commit()

        total_after = cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};").fetchone()[0]
        print(f"Offres insérées : {len(rows_to_insert)}")
        print(f"Doublons ignorés : {skipped_duplicates}")
        print(f"Total offres dans '{TABLE_NAME}' : {total_after}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()