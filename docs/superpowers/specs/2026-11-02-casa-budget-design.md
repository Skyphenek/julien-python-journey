# Casa Binomerie — Budget de la maison (courses et repas de la semaine)

Décisions du 02/11/2026 (Julien) : chiffres **estimés, zéro saisie** (option A) ; un **5ᵉ onglet « Budget »** dans la
barre du bas **et** une ligne sur Aujourd'hui ; **pas d'objectif** de budget pour l'instant (à fixer après 3-4 semaines
de chiffres) ; un **journal des achats** ; forfaits **35 € la livraison, 60 € le resto** pour deux.

## Le problème

Julien et Laetitia veulent savoir combien leur ont coûté les courses et les repas de la semaine, et suivre l'évolution
— en particulier la part livraison, que Casa cherche à faire baisser (objectif : 1 Deliveroo par semaine au plus).
L'app ne garde aucun montant : un article coché dans Courses n'a pas de prix, « vider les pris » le supprime, et un
dîner « Commandé » ne dit pas combien il a coûté.

## Ce qui change pour eux

- **Rien à saisir.** Les montants sont des estimations : le prix d'un panier parisien (`prix_paris.py`) pour chaque
  article coché, un forfait pour chaque commande ou resto.
- **Onglet Budget** (barre du bas : Aujourd'hui, Dîners, Courses, Budget, Vadrouille) :
  - en haut : le total de cette semaine, la moyenne des 4 semaines précédentes, l'économie de la semaine par rapport à
    tout faire livrer ;
  - un graphique en barres empilées (courses, commandes et restos) sur les 12 dernières semaines ;
  - le tableau semaine par semaine, la semaine en cours en premier.
- **Sur Aujourd'hui** : « Cette semaine : 82 € · dont livraison 35 € », qui ouvre l'onglet.

## Les chiffres (semaine du lundi au dimanche, heure de Paris)

| Colonne | Calcul |
|---|---|
| Courses | Somme des prix estimés des articles cochés (pris) dans la semaine. Un article hors du prix de référence compte 0 € et est signalé (« 3 articles sans prix »). |
| Commandes et restos | Repas marqués « Commandé » × 35 € (`LIVRAISON_DEUX`) + repas marqués « Dehors » × 60 € (`FORFAIT_RESTO`). Tous moments (dîner, déjeuner, brunch). |
| Total | Courses + commandes et restos. |
| Repas maison | Nombre de repas « Fait maison » de la semaine. |
| Coût d'un repas maison | Moyenne, sur ces repas, de la somme des `cout_repas` de leurs plats ; vide s'il n'y en a pas. |

- **Pas de double comptage** : les courses servent à faire les repas maison ; le coût des repas maison est affiché pour
  comparer, jamais ajouté au total.
- **Économie de la semaine** = repas maison × 35 € − somme de leurs coûts estimés.
- **Moyenne des 4 dernières** : semaines complètes précédant la semaine en cours (moins de 4 si l'historique est court).
- **Historique** : commandes et restos depuis le 27/10/2026 (issues déjà notées) ; courses à partir de la mise en
  service seulement (les semaines d'avant affichent 0 € de courses, signalé « pas encore suivi »).

## Données

```sql
-- Le journal des achats (02/11/2026) : chaque article coché dans Courses, son prix estimé, le jour.
CREATE TABLE IF NOT EXISTS achats (
    id          SERIAL        PRIMARY KEY,
    article     TEXT          NOT NULL,          -- id de l'article coché (pas de clé étrangère : il peut être supprimé)
    nom         TEXT          NOT NULL,
    prix        NUMERIC(8,2),                    -- prix estimé (prix_paris.prix_de) ; NULL hors catalogue
    jour        DATE          NOT NULL,          -- le jour à Paris où il a été coché
    cree_le     TIMESTAMPTZ   NOT NULL DEFAULT now()
);
```

- **Coché** (pris passe de faux à vrai, dans `db.enregistrer_article`) : une ligne, `jour` = la date du jour à Paris.
- **Décoché** (pris repasse à faux) : la ligne de cet article pour ce jour-là est supprimée (un coché par erreur ne
  compte pas). Un article décoché un autre jour que celui de son achat garde son achat.
- **Vider les pris** et le retour des habituels ne touchent pas au journal.
- Pas de reprise : le journal commence vide.

## Écrans

- **Budget** (page servie par le serveur, comme Aujourd'hui) : chiffres du haut, graphique SVG dessiné côté serveur
  (pas de bibliothèque), tableau. Largeur iPhone sans débordement ; mode sombre via les couleurs du hub.
- **Aujourd'hui** : la ligne budget sous le bloc « À acheter pour aujourd'hui » ; absente tant que le total de la
  semaine est nul.
- `VERSION_PAGE` +1.

## Hors périmètre

- Saisie des vrais montants (tickets, montant d'une commande) et lecture de photo de ticket : plus tard, si les
  estimations ne suffisent pas.
- Objectif de budget hebdomadaire : après 3-4 semaines de chiffres.
- Dépenses hors courses et repas (factures, ménage…).

## Tests

- Journal : coché → une ligne avec prix estimé ; décoché le même jour → supprimée ; vider les pris → journal intact ;
  article hors catalogue → prix NULL.
- Calcul : semaines du lundi, courses, commandes × 35, restos × 60, total, repas maison et coût moyen, économie,
  moyenne des 4 précédentes, articles sans prix.
- Pages : onglet Budget dans la barre (5 entrées), page Budget (chiffres, graphique, tableau), ligne sur Aujourd'hui.
- Démo sur copie des données de prod, testée par Julien avant push/PR/merge.
