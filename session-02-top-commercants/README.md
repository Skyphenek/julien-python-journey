# Session 02 — Top Commerçants

Deuxième script Python de ma série d'apprentissage. Extension du Revolut Analyzer — classement des commerçants par dépenses.

## Ce que ça fait
Lit un export CSV Revolut, agrège les dépenses par commerçant et affiche le top 10 trié par montant décroissant.

## Concepts appris
- Dictionnaires Python — création, accès, accumulation par clé
- Pattern GROUP BY à la main (équivalent SQL sans base de données)
- sorted() avec key=lambda pour trier par valeur
- Slices [:10] pour limiter les résultats (équivalent LIMIT)
- Git init, add, commit, push — premier push sur GitHub

## Exécuter
```
python3 top_commercants.py
```

Note : revolut.csv n'est pas commité (données personnelles).
