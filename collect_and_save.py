import os
import pandas as pd

print("Dossier actuel :", os.getcwd())
print("Fichiers disponibles :", os.listdir("data"))

df = pd.read_csv("data/data_propre.csv", encoding="utf-8-sig")

print("Nombre de lignes :", len(df))
print("Colonnes :", df.columns.tolist())
print(df.head())