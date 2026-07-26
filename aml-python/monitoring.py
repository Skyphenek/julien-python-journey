"""Monitoring AML — regrouper des transactions par client et flagger les seuils.

Application Python des concepts Exercism (dicts + boucles) sur un cas AML réel.
Équivalent SQL : SELECT client, SUM(montant), COUNT(*) FROM tx GROUP BY client.

Données FICTIVES de démo — à remplacer par un vrai export (CSV/Snowflake) ensuite.
"""

# Jeu de données de démo : chaque transaction est un dict.
# (Comme une ligne de table : client, montant en €, type.)
TRANSACTIONS = [
    {"client": "Acme Ltd",   "montant": 4200,  "type": "virement"},
    {"client": "Globex",     "montant": 800,   "type": "carte"},
    {"client": "Acme Ltd",   "montant": 6500,  "type": "virement"},
    {"client": "Initech",    "montant": 300,   "type": "carte"},
    {"client": "Globex",     "montant": 9500,  "type": "virement"},
    {"client": "Acme Ltd",   "montant": 1200,  "type": "carte"},
    {"client": "Globex",     "montant": 2000,  "type": "virement"},
    {"client": "Initech",    "montant": 150,   "type": "carte"},
]

SEUIL_ALERTE = 10000  # au-dessus de ce total cumulé, on lève une alerte


def total_par_client(transactions):
    """Regrouper les transactions par client et sommer les montants.

    Équivalent SQL : SELECT client, SUM(montant) FROM tx GROUP BY client.
    Retourne un dict {client: total}.
    """
    total = {}
    for tx in transactions:
        client = tx["client"]
        montant = tx["montant"]
        if client in total:
            total[client] = total[client] + montant
        else:
            total[client] = montant
    return total


def clients_en_alerte(totaux, seuil):
    """Renvoyer la liste des clients dont le total dépasse le seuil.

    Équivalent SQL : ... GROUP BY client HAVING SUM(montant) > seuil.
    """
    alertes = []
    for client, montant in totaux.items():
        if montant > seuil:
            alertes.append(client)
    return alertes


def main():
    """Point d'entrée : lance le monitoring sur les données de démo."""
    totaux = total_par_client(TRANSACTIONS)
    print("Totaux par client :", totaux)

    alertes = clients_en_alerte(totaux, SEUIL_ALERTE)
    print(f"Clients en alerte (> {SEUIL_ALERTE} €) :", alertes)


if __name__ == "__main__":
    main()
