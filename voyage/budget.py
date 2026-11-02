"""Casa Binomerie — Budget de la maison : combien ont coûté les courses et les repas, semaine par semaine.

Chiffres estimés, zéro saisie (spec 2026-11-02-casa-budget-design.md) :
- courses : le journal des achats (db.lire_achats), au prix d'un panier parisien (prix_paris) ;
- commandes et restos : les repas marqués « Commandé » (35 € pour deux) ou « Dehors » (60 € pour deux) ;
- repas maison : affichés pour comparer (coût moyen de leurs recettes), jamais ajoutés au total.
Semaine du lundi au dimanche.
"""
import math
from datetime import timedelta

from diners import LIVRAISON_DEUX
from prix_paris import cout_repas

FORFAIT_RESTO = 60          # un resto pour deux à Paris : l'ordre de grandeur
SEMAINES = 12


def lundi(jour):
    return jour - timedelta(days=jour.weekday())


def euros(x):
    """Arrondi à l'euro, le demi vers le haut (round() de Python arrondit 36,5 à 36)."""
    return f"{math.floor(x + 0.5)} €"


def semaines_budget(achats, repas, plats, aujourd_hui, n=SEMAINES):
    """Les n dernières semaines, la semaine en cours en premier (voir la docstring du module)."""
    premier_achat = min((a["jour"] for a in achats), default=None)
    semaines = []
    for k in range(n):
        debut = lundi(aujourd_hui) - timedelta(weeks=k)
        fin = debut + timedelta(days=6)
        achetes = [a for a in achats if debut <= a["jour"] <= fin]
        vecus = [r for r in repas if debut <= r["jour"] <= fin]
        commandes = sum(1 for r in vecus if r["issue"] == "commande")
        restos = sum(1 for r in vecus if r["issue"] == "dehors")
        maison = [r for r in vecus if r["issue"] == "fait"]
        couts = [sum(cout_repas(plats[i]["ingredients"], plats[i]["recette"]) for i in r["plats"] if i in plats)
                 for r in maison if any(i in plats for i in r["plats"])]
        courses = round(sum(a["prix"] or 0 for a in achetes), 2)
        livraison = commandes * LIVRAISON_DEUX + restos * FORFAIT_RESTO
        semaines.append({
            "lundi": debut, "courses": courses, "courses_suivies": premier_achat is not None and fin >= premier_achat,
            "sans_prix": sum(1 for a in achetes if a["prix"] is None),
            "commandes": commandes, "restos": restos, "livraison": livraison, "total": round(courses + livraison, 2),
            "maison": len(maison), "cout_maison": round(sum(couts) / len(couts), 2) if couts else None,
            "economie": round(len(couts) * LIVRAISON_DEUX - sum(couts), 2)})
    return semaines


def moyenne_precedentes(semaines, k=4):
    """Le total moyen des k semaines avant la semaine en cours, celles sans aucun chiffre ignorées ; None sinon."""
    precedentes = [s for s in semaines[1:1 + k] if s["total"] or s["maison"]]
    return round(sum(s["total"] for s in precedentes) / len(precedentes), 2) if precedentes else None
