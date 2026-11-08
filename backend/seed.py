"""Données de DÉMONSTRATION fictives : villes réelles, entreprises inventées, titres réalistes.
Usage : python -m backend.seed --reset   (régénère les données)"""
import random
import sys
from datetime import date, timedelta

from .database import count_offers, init_db, insert_offers, reset_offers

rng = random.Random(2026)  # graine fixe -> mêmes données à chaque génération

CITIES = [("Casablanca", 30), ("Rabat", 18), ("Marrakech", 11), ("Tanger", 10), ("Fès", 7),
          ("Agadir", 7), ("Kénitra", 4), ("Tétouan", 4), ("Oujda", 3), ("Meknès", 3)]

COMPANIES = [
    "Atlas Digital Studio", "Medina Data Labs", "Souss Tech Solutions", "Kasbah Cloud", "Argan Analytics",
    "Tanjaoui Software", "Anfa Systems", "Rif Cyber Defense", "Zellige UX Lab", "Oasis Commerce",
    "Anfa Digital Agency", "Bouregreg Fintech", "Menara Media Group", "Sahara AI Works", "Chefchaouen Creative",
    "Fès Innovation Hub", "Oumnia Consulting IT", "Jbel Software Factory", "Dar Algorithm", "Maghreb Growth Marketing",
    "Taza Cloud Services", "Essaouira Web Studio", "Hay Riad Labs", "Ifrane Learning Tech", "Gueliz Digital",
    "Agdal Software", "Maarif Tech Partners", "Corniche Cyber", "Nador Data Services", "Atlas Telecom Services",
]

DOMAINS = {  # nom: (poids, intitulés, compétences)
    "Data & IA": (22, ["Data Analyst", "Data Scientist", "Ingénieur Machine Learning", "Data Engineer", "Analyste BI", "Ingénieur NLP"],
                  ["Python", "SQL", "Pandas", "Power BI", "scikit-learn", "TensorFlow", "Spark", "Airflow", "Tableau", "NLP", "MLOps", "Excel"]),
    "Développement web & mobile": (24, ["Développeur Full-Stack", "Développeur Front-End React", "Développeur Back-End Node.js", "Développeur Flutter", "Développeur Laravel", "Développeur Java Spring"],
                                   ["JavaScript", "React", "Node.js", "TypeScript", "PHP", "Laravel", "Java", "Spring Boot", "Flutter", "Git", "REST API", "SQL"]),
    "Marketing digital & SEO": (14, ["Chargé de marketing digital", "Spécialiste SEO", "Traffic Manager", "Community Manager", "Content Strategist"],
                                ["SEO", "Google Ads", "Meta Ads", "Google Analytics", "Content marketing", "Emailing", "Canva", "Copywriting"]),
    "Cloud & DevOps": (8, ["Ingénieur DevOps", "Ingénieur Cloud", "Administrateur Systèmes"],
                       ["Docker", "Kubernetes", "AWS", "Azure", "CI/CD", "Linux", "Terraform", "Git", "Python"]),
    "Cybersécurité": (7, ["Analyste SOC", "Consultant Cybersécurité", "Pentester Junior"],
                      ["Sécurité réseau", "SIEM", "Pentest", "ISO 27001", "Linux", "Python", "Firewall", "OWASP"]),
    "UX/UI Design": (8, ["UX/UI Designer", "Product Designer", "Designer Graphique Digital"],
                     ["Figma", "Design System", "Prototypage", "Recherche utilisateur", "Adobe XD", "Photoshop", "Illustrator"]),
    "Communication digitale": (10, ["Chargé de communication digitale", "Social Media Manager", "Rédacteur Web"],
                               ["Réseaux sociaux", "Rédaction web", "Canva", "Création de contenu", "Montage vidéo", "Veille", "Community management"]),
    "E-commerce & Growth": (7, ["Growth Marketer", "E-commerce Manager", "Analyste CRM"],
                            ["Shopify", "CRM", "A/B testing", "Google Analytics", "Excel", "SQL", "Automatisation", "n8n"]),
}

CONTRACTS = [("PFE", 25), ("Stage d'été", 15), ("Pré-embauche", 12), ("Stage rémunéré", 18), ("CDI", 15), ("CDD", 8)]
SALARY = {  # contrat: (min, max, probabilité de valeur manquante)
    "PFE": (2000, 4000, 0.55), "Stage d'été": (1500, 3000, 0.70), "Pré-embauche": (3000, 6000, 0.35),
    "Stage rémunéré": (2500, 5000, 0.0), "CDI": (6000, 14000, 0.35), "CDD": (5000, 9000, 0.40),
}
MISSIONS = ["contribuer à des projets clients au sein d'une équipe agile",
            "concevoir et livrer des fonctionnalités à forte valeur ajoutée",
            "participer à la veille et à l'amélioration continue des outils internes"]
SOURCES = ["Site carrière", "Job board", "Réseau professionnel", "Centre de carrière universitaire"]


def _pick(pairs):
    names, weights = zip(*pairs)
    return rng.choices(names, weights=weights)[0]


def _title(contract, base):
    return {"PFE": f"Stage PFE – {base}", "Stage d'été": f"Stage d'été – {base}",
            "Pré-embauche": f"Stage pré-embauche – {base}", "Stage rémunéré": f"Stage rémunéré – {base}",
            "CDI": f"{base} Junior (CDI)", "CDD": f"{base} (CDD)"}[contract]


def generate(n: int = 240) -> list[dict]:
    today, rows = date.today(), []
    for i in range(n):
        domain = rng.choices(list(DOMAINS), weights=[v[0] for v in DOMAINS.values()])[0]
        _, titles, skills_pool = DOMAINS[domain]
        contract, city, company = _pick(CONTRACTS), _pick(CITIES), rng.choice(COMPANIES)
        title = _title(contract, rng.choice(titles))
        skills = rng.sample(skills_pool, k=rng.randint(4, 6))
        level = rng.choice(["Bac+5", "Bac+4"] if contract == "PFE" else ["Bac+3", "Bac+4", "Bac+5"])
        lo, hi, p_missing = SALARY[contract]
        salary = None if rng.random() < p_missing else int(round(rng.uniform(lo, hi) / 100) * 100)
        posted = today - timedelta(days=min(180, int(rng.expovariate(1 / 40))))
        row = {
            "title": title, "company": company, "city": city, "domain": domain, "contract": contract,
            "kind": "Emploi" if contract in ("CDI", "CDD") else "Stage", "level": level,
            "salary_mad": salary, "remote": rng.random() < 0.18, "skills": ", ".join(skills),
            "description": (f"{company} recherche un(e) candidat(e) pour « {title} » à {city}. "
                            f"Missions : {rng.choice(MISSIONS)}. Profil {level}, maîtrise de {', '.join(skills[:3])}."),
            "source": rng.choice(SOURCES), "url": f"https://example.com/offres/{i + 1}",
            "posted_date": posted, "deadline": posted + timedelta(days=rng.randint(20, 60)),
            "collected_date": min(today, posted + timedelta(days=rng.randint(0, 3))), "is_demo": True,
        }
        for field, p in [("domain", .04), ("city", .03), ("level", .08), ("posted_date", .05), ("deadline", .25), ("skills", .02)]:
            if rng.random() < p:
                row[field] = None  # valeurs manquantes réalistes, volontaires
        rows.append(row)
    return rows


def seed_if_empty():
    init_db()
    if count_offers() == 0:
        insert_offers(generate())


if __name__ == "__main__":
    init_db()
    if "--reset" in sys.argv:
        reset_offers()
        insert_offers(generate())
    elif count_offers() == 0:
        insert_offers(generate())
    print(f"{count_offers()} offres de démonstration en base.")
