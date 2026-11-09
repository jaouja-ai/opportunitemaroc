# OPPORTUNITEMAROC

Plateforme pour étudiants marocains : **centraliser** les offres de stage et d'emploi digital, les **filtrer**, **adapter son CV avec l'IA** et le télécharger en PDF, **discuter avec un assistant IA** et **visualiser le marché**.


## Sommaire

1. [Fonctionnalités](#fonctionnalités)
2. [Architecture](#architecture)
3. [Structure du projet](#structure-du-projet)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Exécution](#exécution)
7. [Utilisation](#utilisation)
8. [Données : collecte, nettoyage, export](#données--collecte-nettoyage-export)
9. [Intelligence artificielle](#intelligence-artificielle)
10. [Déploiement](#déploiement)
11. [Dépannage](#dépannage)

## Fonctionnalités

| Page | Description |
|---|---|
| **Offres** | Liste des offres avec filtres (type, contrat, ville, domaine, niveau, télétravail, rémunération, date) |
| **Générateur de CV** | Adapte le CV à une offre ciblée (IA ou règles) et l'exporte en PDF |
| **Statistiques & Insights** | Indicateurs clés et dashboard interactif (villes, domaines, salaires, compétences, qualité des données) |
| **Assistant IA** | Chatbot qui répond sur les offres de la base, le CV et les entretiens, et affiche les offres pertinentes sous forme de cartes |

## Architecture

```
Navigateur ──► Streamlit (8501)  ──HTTP──►  FastAPI (8000) ──► SQLAlchemy ──► SQLite
                │  Offres + filtres            │  /api/offers, /api/filters, /api/stats
                │  Générateur de CV            │  /api/cv/generate ──► IA (API compatible OpenAI) ou règles
                │  Statistiques & Insights     │  /api/cv/pdf      ──► ReportLab
                │  Assistant IA                │  /api/chat        ──► IA (API compatible OpenAI)
                └─ iframe ───────────────────► └─ /dashboard (Dash monté dans FastAPI)
```

L'interface ne touche jamais la base de données : tout passe par l'API.

## Structure du projet

| Élément | Rôle |
|---|---|
| `backend/` | API FastAPI, base de données, nettoyage des données, IA, PDF, chatbot, données de démonstration |
| `dashboard/` | Graphiques interactifs Dash (servis par l'API sur `/dashboard`) |
| `frontend/` | Interface Streamlit (`streamlit_app.py`, `chatbot_ui.py`, client API, styles) |
| `.streamlit/config.toml` | Thème bleu/blanc |
| `run.py` | Lance l'API et Streamlit en une commande |
| `collect_and_save.py` | Nettoie et enregistre de vraies offres dans la base |
| `exporter_donnees.py` | Exporte `data.csv` (brut) et `traiter.csv` (nettoyé) |
| `requirements.txt` | Dépendances Python |
| `.env.example` | Modèle du fichier de configuration |

## Installation

**Prérequis :** Python 3.10 ou plus récent (testé avec 3.13), pip, et un terminal (PowerShell sous Windows).

Dans le dossier du projet, ouvert dans VS Code :

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

Mac / Linux :

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

> Les commandes utilisent directement `venv\Scripts\python` : inutile d'activer l'environnement, ce qui évite l'erreur « exécution de scripts désactivée » sous PowerShell.

## Configuration

Copier le modèle puis le remplir :

```powershell
copy .env.example .env
```

| Variable | Rôle | Obligatoire |
|---|---|---|
| `LLM_API_KEY` | Clé de l'API d'IA (CV adapté + assistant) | Non (sans clé : CV par règles, chatbot désactivé) |
| `LLM_BASE_URL` | Adresse de l'API compatible OpenAI | Non (ex. Groq : `https://api.groq.com/openai/v1`) |
| `LLM_MODEL` | Nom du modèle | Non (ex. `llama-3.1-8b-instant`) |
| `DATABASE_URL` | Base de données (SQLite par défaut ; PostgreSQL : `postgresql+psycopg2://user:pass@host/db`) | Non |
| `API_URL` | Adresse de l'API vue par Streamlit | Non (`http://localhost:8000` en local) |
| `PUBLIC_API_URL` | Adresse publique de l'API (iframe du dashboard) | Non (en déploiement seulement) |

Exemple de `.env` pour Groq :

```
LLM_API_KEY=votre_clé
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```

🔒 Le fichier `.env` est dans `.gitignore` : **ne jamais envoyer une clé sur GitHub** ni la partager. Les noms de modèles évoluent : vérifier la liste du fournisseur.

## Exécution

```powershell
.\venv\Scripts\python run.py
```

- Application : http://localhost:8501 (le navigateur s'ouvre automatiquement)
- API et documentation interactive : http://localhost:8000/docs
- `Ctrl+C` arrête tout.

Au premier lancement, la base SQLite (`opportunitemaroc.db`) est créée et remplie avec 240 offres de démonstration.

## Utilisation

1. **Offres** : filtrer dans la barre latérale, ouvrir « Détails de l'offre », cliquer sur « Adapter mon CV ».
2. **Générateur de CV** : choisir l'offre, renseigner son profil, cliquer sur « Adapter mon CV », modifier le résumé, puis « Télécharger le CV (PDF) ».
3. **Statistiques & Insights** : consulter les indicateurs et les graphiques interactifs.
4. **Assistant IA** : cliquer sur une suggestion ou poser sa question (ex. « Quels stages en Data à Casablanca ? »).

## Données : collecte, nettoyage, export

**Valeurs manquantes** (`backend/data_processing.py`) :

| Colonne | Traitement | Visible dans l'interface |
|---|---|---|
| Titre | Offre supprimée | — |
| Ville, domaine, niveau, entreprise | « Non renseigné » | Barre/part grise + note sous le graphique |
| Date de publication | Remplacée par la date de collecte | Note « x date(s) estimée(s) » |
| Rémunération, date limite | Laissées vides (jamais inventées) | Badge « Rémunération non renseignée » ; médiane sur valeurs connues uniquement |
| Compétences | Chaîne vide | « non renseignées » |

**Scripts utiles :**

```powershell
.\venv\Scripts\python collect_and_save.py     # nettoie et insère de vraies offres (is_demo = False)
.\venv\Scripts\python exporter_donnees.py     # génère data.csv (brut) et traiter.csv (nettoyé)
.\venv\Scripts\python -m backend.seed --reset # régénère uniquement la démo (240 offres fictives)
```

### Brancher de vraies offres

1. Collecter légalement (API officielles, flux autorisés, saisie manuelle). Pas de scraping des sites qui l'interdisent (ex. LinkedIn).
2. Insérer avec `backend.database.insert_offers([...])` en mettant `is_demo=False` (même format que `backend/seed.py`, voir `collect_and_save.py`).
3. `--reset` ne touche jamais aux vraies offres. Le badge « démo » reste affiché tant qu'au moins une offre fictive est en base.

## Intelligence artificielle

- **CV adapté** : l'IA reformule sans inventer. Toute compétence absente du profil est supprimée de la réponse. Sans clé ou en cas d'erreur, retour automatique à un mode par règles (compétences communes mises en avant).
- **Assistant IA** (`POST /api/chat`) : la question est comparée aux offres de la base, les plus pertinentes sont transmises au modèle, qui ne doit citer que ces offres. L'interface affiche ensuite ces offres en cartes.
- Compatible avec toute API au format OpenAI (Groq, OpenAI, Gemini, xAI…) via `LLM_BASE_URL`.

## Déploiement

Deux services (un seul port public par service). Build commun : `pip install -r requirements.txt`.

| Service | Hébergeur conseillé | Commande de démarrage | Variables |
|---|---|---|---|
| API + dashboard | Render | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `DATABASE_URL` (optionnel) |
| Interface | Streamlit Cloud (fichier principal `frontend/streamlit_app.py`) | automatique | `API_URL` et `PUBLIC_API_URL` = adresse publique de l'API |

Sur Streamlit Cloud, ces variables se renseignent dans *Settings → Secrets* :

```toml
API_URL = "https://votre-api.onrender.com"
PUBLIC_API_URL = "https://votre-api.onrender.com"
```

**À savoir sur les offres gratuites :**
- Le service s'endort après inactivité (premier chargement de 30 à 60 s) ; l'interface attend alors son réveil.
- Le disque est éphémère : SQLite repart de la démo à chaque redémarrage. Pour garder les données, utiliser PostgreSQL via `DATABASE_URL` (ajouter `psycopg2-binary` aux dépendances).

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `error while attempting to bind` / `Port 8501 is not available` | Une ancienne instance tourne encore | `taskkill /F /IM python.exe` puis relancer `run.py` |
| Chatbot : « Erreur 503 : LLM_API_KEY manquante » | Clé absente du `.env` | Renseigner `LLM_API_KEY`, relancer |
| Chatbot : `404 Not Found` sur `/api/chat` | Route non branchée dans `backend/main.py` | Ajouter `app.include_router(chatbot_router)` avant tout `app.mount(...)` |
| Chatbot : « Erreur du modèle … 404 » | Nom de modèle refusé par le fournisseur | Changer `LLM_MODEL` selon la liste du fournisseur |
| « L'API ne répond pas » en ligne | Service gratuit endormi | Attendre 1 minute puis recharger |
| Page blanche sur Streamlit Cloud | `API_URL` absent ou erroné dans les Secrets | Renseigner l'adresse publique de l'API |
