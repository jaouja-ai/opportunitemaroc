# OPPORTUNITEMAROC

Plateforme pour étudiants marocains : centraliser les offres de stages et d'emploi digital, les filtrer, adapter son CV avec l'IA, le télécharger en PDF et visualiser le marché.

>  Les offres fournies sont des données de démonstration FICTIVES** (villes réelles, entreprises inventées, titres réalistes). L'interface l'indique par un badge. Voir « Brancher de vraies offres » plus bas.

 Architecture


Navigateur ──► Streamlit (8501)  ──HTTP──►  FastAPI (8000) ──► SQLAlchemy ──► SQLite
                │  Offres + filtres            │  /api/offers, /api/filters, /api/stats
                │  Générateur de CV            │  /api/cv/generate  ──► IA (API compatible OpenAI) ou règles
                │  Statistiques & Insights     │  /api/cv/pdf       ──► ReportLab
                └─ iframe ───────────────────► └─ /dashboard  (Dash monté dans FastAPI)


| Dossier | Rôle |
| `backend/` | API, base de données, nettoyage des données, IA, PDF, données de démonstration |
| `dashboard/` | Graphiques interactifs Dash (servis par l'API sur `/dashboard`) |
| `frontend/` | Interface Streamlit (3 pages) |
| `.streamlit/config.toml` | Thème bleu/blanc |
| `run.py` | Lance API + Streamlit en une commande |

 Design system

| Élément | Valeur |

| Bleu principal | `#1E3A8A` |
| Bleu accent | `#3B82F6` |
| Fonds | `#FFFFFF` et `#F8FAFC` |
| Texte | `#1E293B` |
| Gris « non renseigné » | `#94A3B8` |
| Série de bleus (camemberts) | `#1E3A8A #2563EB #3B82F6 #60A5FA #93C5FD #BFDBFE` |

 Valeurs manquantes (`backend/data_processing.py`)

| Colonne | Traitement | Visible dans l'interface |

| Titre | Offre supprimée 
| Ville, domaine, niveau, entreprise | « Non renseigné » | Barre/part grise + note sous le titre du graphique |
| Date de publication | Remplacée par la date de collecte | Note « x date(s) estimée(s) » |
| Rémunération, date limite | Laissées vides (jamais inventées) | Badge « Rémunération non renseignée » ; médiane calculée sur valeurs connues uniquement |
| Compétences | Chaîne vide | « non renseignées » |

Le graphique « Qualité des données » affiche le % de valeurs manquantes par colonne.

 Installation (Windows / PowerShell)

Dans le dossier du projet, ouvert dans VS Code :

powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python run.py


(Sans activer l'environnement : cela évite l'erreur « exécution de scripts désactivée ».)  
Mac/Linux : `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && ./venv/bin/python run.py`

Le navigateur s'ouvre sur http://localhost:8501. API et documentation : http://localhost:8000/docs. `Ctrl+C` arrête tout.

 Activer l'IA (optionnel)

Sans clé, le CV est adapté par règles simples (compétences communes mises en avant) : l'application fonctionne déjà.  
Pour l'IA : copier `.env.example` en `.env` et renseigner `LLM_API_KEY` (+ `LLM_BASE_URL` / `LLM_MODEL` pour Groq, xAI…).  
Garde-fous : l'IA reformule sans inventer — toute compétence absente du profil est supprimée de la réponse ; en cas d'erreur, retour automatique au mode règles.

 Brancher de vraies offres

1. Collecter légalement (API officielles, flux autorisés, saisie manuelle — pas de scraping des sites qui l'interdisent, ex. LinkedIn).
2. Insérer avec `backend.database.insert_offers([])` en mettant `is_demo=False` (même format que `backend/seed.py`).
3. `python -m backend.seed --reset` régénère uniquement la démo (240 offres fictives) ; le badge reste affiché tant qu'au moins une offre fictive est en base, et `--reset` ne touche jamais aux vraies offres.

Déploiement (Render, Railway…)

Deux services web (un seul port public par service) :

| Service | Commande de démarrage | Variables |

| API + Dash | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` | `LLM_API_KEY` (optionnel), `DATABASE_URL` (optionnel) |
| Interface | `streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0` | `API_URL` = adresse interne de l'API, `PUBLIC_API_URL` = adresse publique de l'API |

Build commun : `pip install -r requirements.txt`.  
Sur les offres gratuites, le disque est éphémère : SQLite repart de la démo à chaque redémarrage. Pour garder des données, utiliser PostgreSQL via `DATABASE_URL` (ex. `postgresql+psycopg2://…`, ajouter `psycopg2-binary` aux dépendances).

 
