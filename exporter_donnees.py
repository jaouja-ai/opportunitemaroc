import pandas as pd

def charger_offres():
    chemin = "data_propre.csv"

    df = pd.read_csv(
        chemin,
        encoding="utf-8-sig"
    )

    df.columns = df.columns.str.strip().str.lower()

    df = df.drop_duplicates()

    return df
df = charger_offres()

print(df.head())
print("Nombre d'offres :", len(df))