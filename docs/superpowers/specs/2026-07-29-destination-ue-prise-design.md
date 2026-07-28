# Design — UE auto + type de prise par destination

## Problème

Deux frictions dans `valise.py` :
1. La question "Destination hors UE ? (o/n)" est posée à la main alors que
   ça se déduit du pays.
2. La checklist ne dit pas **quel adaptateur de prise** emporter. Julien veut
   savoir, pour une destination donnée, s'il prend un adaptateur FR / US / UK /
   universel.

## Décisions validées (brainstorm 2026-07-29)

- **Structure** : tables parallèles + garde-fou. On ajoute `PAYS_UE` et
  `PAYS_VERS_PRISE` à côté des tables zone existantes. Un garde-fou signale les
  pays qui ont une zone mais pas de prise renseignée. (Pas de refonte en table
  riche unique — incrémental, colle au style actuel.)
- **Sortie prise** : l'**adaptateur à emporter depuis la France** (actionnable),
  ex. Vietnam → "universel / US". Pas le standard technique brut.
- **Portée** : pays et États d'abord. Les villes non couvertes affichent
  "à vérifier" et le garde-fou les liste. Aucune donnée inventée.

## Architecture

### UE — déduction, plus de question

`PAYS_UE` = set des pays membres de l'UE (France, Italie, Espagne, ...).

```python
def statut_ue(destination):
    """ue / hors_ue / inconnu à partir de la destination."""
    if destination in PAYS_UE:
        return "ue"
    if destination in PAYS_VERS_ZONE:   # pays connu absent de l'UE -> hors UE
        return "hors_ue"
    return "inconnu"                     # ville ou non couvert -> défaut prudent
```

Dans `main`, on **supprime la question** `hors UE ? (o/n)` et on calcule :
`hors_ue = statut_ue(destination) != "ue"`. Un statut `inconnu` (ville non
couverte) → `hors_ue = True` (passeport, défaut sûr) + un `⚠️` "statut UE à
vérifier". `PAYS_UE` accepte aussi des villes si Julien veut en couvrir plus tard
(la fonction teste juste l'appartenance).

`faire_valise` **ne change pas** : elle reçoit toujours `hors_ue` en booléen.

### Prise — quel adaptateur emporter

`PAYS_VERS_PRISE` = pays → libellé d'adaptateur ("aucun (mêmes prises qu'en
France)", "UK", "US (110V)", "universel", "universel / US", ...).

```python
def adaptateur_pour(destination):
    """Libellé de l'adaptateur à emporter depuis la France, ou 'à vérifier'."""
    if destination in PAYS_VERS_PRISE:
        return PAYS_VERS_PRISE[destination]
    return "à vérifier"
```

Affiché dans l'en-tête de la page HTML (info niveau destination), sous le titre :
`🔌 Adaptateur : <libellé>`. L'objet "adaptateur de prise" reste dans la
checklist par personne (déjà fait) ; l'en-tête indique lequel prendre.

Données prise : valeurs usuelles (à revérifier ponctuellement). Continent
européen / Maghreb (type C/E/F) → "aucun". Îles britanniques + Malte + EAU +
Singapour + Malaisie (type G) → "UK". Amériques + Japon (type A/B) → "US".
Asie du Sud-Est mixte (Thaïlande, Vietnam, Cambodge...) → "universel".

### Garde-fou prise

```python
def pays_sans_prise():
    """Pays/États qui ont une zone mais aucune prise renseignée."""
    return set(PAYS_VERS_ZONE) - set(PAYS_VERS_PRISE)
```

Appelé au démarrage de `main`, comme `objets_sans_rayon` : un `⚠️` liste les
pays à compléter. (Pas de garde-fou UE : l'absence d'un pays dans `PAYS_UE`
est significative = hors UE, ce n'est pas un trou.)

## Tests / validation manuelle

- Vietnam → hors UE (passeport, sans question posée) + "Adaptateur : universel".
- Italie → UE (carte d'identité) + "Adaptateur : aucun".
- Une ville non couverte (ex. Bangkok) → passeport + "⚠️ statut UE à vérifier"
  + "Adaptateur : à vérifier".
- `pays_sans_prise()` vide une fois toutes les entrées `PAYS_VERS_ZONE` remplies.

## Hors scope

- Couverture prise/UE des ~40 villes (via lien ville→pays) : plus tard.
- Tension/voltage détaillé, fréquence : on se limite au libellé d'adaptateur
  (mention "110V" quand ça compte, sans plus).
