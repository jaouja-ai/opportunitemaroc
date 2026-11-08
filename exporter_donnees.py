import pandas as pd
from backend.database import read_offers_df
from backend.data_processing import clean_offers

def main():
    print("🔄 Extraction des données de l'application...")

    # 1. Récupération des données brutes depuis la base de données de l'application
    df_brutes = read_offers_df()
    
    if df_brutes.empty:
        print("⚠️ Aucune donnée trouvée dans la base de données.")
        return

    print(f"-> {len(df_brutes)} offres récupérées depuis l'application.")

    # 2. Sauvegarde du fichier BRUT : data.csv
    df_brutes.to_csv("data.csv", index=False, encoding="utf-8-sig")
    print("✅ Fichier 'data.csv' (donnees brutes) généré avec succès !")

    # 3. Application du nettoyage via votre module data_processing.py
    df_traitees = clean_offers(df_brutes)

    # 4. Sauvegarde du fichier TRAITÉ : traiter.csv
    df_traitees.to_csv("traiter.csv", index=False, encoding="utf-8-sig")
    print(" Fichier 'traiter.csv' (donnees nettoyees) généré avec succès !")

if __name__ == "__main__":
    main()