import pandas as pd
from backend.database import init_db, insert_offers
from backend.data_processing import clean_offers

def main():
    # Données brutes avec la colonne 'kind' ajoutée
    donnees_brutes = pd.DataFrame([
        {
            "title": "Développeur Backend Python / FastAPI",
            "company": "Marrakech Digital Lab",
            "city": "Marrakech",
            "kind": "Emploi",             # <-- Ajouté ici
            "contract": "CDI",
            "domain": "IT / Développement",
            "level": "Bac+5",
            "salary_mad": 12000,
            "remote": True,
            "skills": "Python, FastAPI, SQL, Git",
            "description": "Nous cherchons un développeur backend motivé basé à Marrakech...",
            "source": "SiteWebExterne",
            "url": "https://example.com/offre-1",
            "posted_date": "2026-11-05",
            "deadline": "2026-12-01",
            "collected_date": "2026-11-08",
            "is_demo": False  # Indique que c'est une vraie offre
        }
    ])

    print(f"-> {len(donnees_brutes)} offre(s) brute(s) récupérée(s).")

    # Nettoyage
    donnees_propres = clean_offers(donnees_brutes)
    donnees_propres["is_demo"] = False

    print(f"-> {len(donnees_propres)} offre(s) après nettoyage.")

    # Enregistrement dans la base de données
    init_db()
    rows_to_insert = donnees_propres.to_dict(orient="records")
    insert_offers(rows_to_insert)
    
    print(" Vraies offres insérées avec succès dans la base de données !")

if __name__ == "__main__":
    main()