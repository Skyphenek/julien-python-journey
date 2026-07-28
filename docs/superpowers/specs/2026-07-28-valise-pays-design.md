# Design — saisie par pays dans valise.py

## Problème

`voyage/valise.py` ne comprend que des noms de ville (`VILLE_VERS_ZONE`). Pour dire
"je pars en Thaïlande", il faut aujourd'hui connaître et taper le nom d'une ville
thaïlandaise précise (ex. "Bangkok") — impossible de raisonner au niveau pays.
Objectif : pouvoir taper un nom de
**pays** (ou d'État US) et obtenir les mêmes types de destination (`chaud`,
`plage`, `ville`, ...) qu'avec une ville, en réutilisant l'infra saisonnière
existante (`ZONES`).

## Décisions validées

- **Saisonnalité** : un pays se comporte comme une ville — il pointe vers une
  **zone climatique** de la table `ZONES` existante, donc les types varient
  toujours selon le mois (hiver/été/...). Pas de table de saisons séparée à créer.
- **Saisie** : un seul prompt `"Destination : "` (au lieu de `"Ville de
  destination : "`). L'utilisateur tape indifféremment une ville ou un pays ; le
  programme cherche dans les deux tables.
- **Portée géographique** : pays européens, nord-africains/Moyen-Orient, Asie du
  Sud-Est, tropicaux (Amériques/îles) — mappés vers une zone unique. Pays au
  climat trop hétérogène pour une seule zone (États-Unis, Indonésie, Brésil,
  Australie, Chine, Inde) sont **volontairement exclus** : rester sur la saisie
  par ville pour ces cas. Exception : les États américains les plus touristiques
  (climat homogène à l'échelle de l'État) sont ajoutés individuellement.

## Architecture

Nouvelle table `PAYS_VERS_ZONE` (pays/État → zone), au même niveau que
`VILLE_VERS_ZONE`, alimentant la même table `ZONES` déjà en place.

```python
PAYS_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Royaume-Uni": "europe_nord", "Irlande": "europe_nord",
    "Pays-Bas": "europe_nord", "Belgique": "europe_nord",
    "Allemagne": "europe_nord", "Danemark": "europe_nord",
    "Suède": "europe_nord", "Norvège": "europe_nord", "Islande": "europe_nord",
    # Europe de l'Ouest continentale
    "France": "europe_ouest", "Luxembourg": "europe_ouest",
    # Montagne / Alpes
    "Suisse": "montagne_alpes", "Autriche": "montagne_alpes", "Slovénie": "montagne_alpes",
    # Méditerranée
    "Italie": "mediterranee", "Espagne": "mediterranee", "Grèce": "mediterranee",
    "Portugal": "mediterranee", "Croatie": "mediterranee", "Malte": "mediterranee",
    "Chypre": "mediterranee",
    # Afrique du Nord / Moyen-Orient désertique
    "Maroc": "afrique_nord", "Tunisie": "afrique_nord", "Égypte": "afrique_nord",
    "Émirats Arabes Unis": "afrique_nord", "Jordanie": "afrique_nord",
    # Asie du Sud-Est
    "Thaïlande": "asie_sud_est", "Vietnam": "asie_sud_est", "Cambodge": "asie_sud_est",
    "Laos": "asie_sud_est", "Myanmar": "asie_sud_est", "Malaisie": "asie_sud_est",
    "Singapour": "asie_sud_est", "Philippines": "asie_sud_est", "Japon": "asie_sud_est",
    "Sri Lanka": "asie_sud_est",
    # Tropical (Amériques / îles)
    "Mexique": "tropical", "Cuba": "tropical", "République Dominicaine": "tropical",
    "Costa Rica": "tropical",
    # États-Unis (pays exclu du mapping, mais États touristiques homogènes inclus)
    "Californie": "usa_ouest", "Floride": "tropical", "Hawaï": "tropical",
    "Nevada": "usa_ouest", "Arizona": "usa_ouest", "Louisiane": "usa_est",
}
```

### Fonction `zone_de`

Remplace l'accès direct `VILLE_VERS_ZONE[ville]` dans `types_pour`. Cherche
d'abord dans les villes (plus précis), puis dans les pays/États.

```python
def zone_de(destination):
    """Trouver la zone climatique d'une ville ou d'un pays."""
    if destination in VILLE_VERS_ZONE:
        return VILLE_VERS_ZONE[destination]
    return PAYS_VERS_ZONE[destination]
```

`types_pour(destination, mois)` appelle `zone_de(destination)` au lieu de
`VILLE_VERS_ZONE[ville]`. Le paramètre `ville` est renommé `destination` par
cohérence (et dans `faire_valise`/`main` si besoin).

### Saisie (`main`)

La boucle de validation devient :

```python
while True:
    destination = input("Destination (ville ou pays) : ")
    if destination in VILLE_VERS_ZONE or destination in PAYS_VERS_ZONE:
        break
    print(f"Destination '{destination}' inconnue, vérifie l'orthographe.")
```

## Erreurs

Comportement inchangé : destination absente des deux tables → message
d'erreur, redemande. Pas de nouveau cas d'erreur introduit.

## Tests / validation manuelle

Pas de suite de tests automatisés existante pour ce script (checklist générée
via `main()` interactif). Validation manuelle attendue à l'implémentation :
- une ville déjà connue (ex. "Paris") continue de fonctionner à l'identique
- un pays neuf (ex. "Thaïlande", janvier → hiver) donne les mêmes types que la
  zone `asie_sud_est` en hiver (`["chaud", "plage"]`)
- une destination inconnue (ni ville ni pays) redemande comme avant

## Hors scope

- Agrégation multi-villes/multi-région au sein d'un même pays (ex. distinguer
  nord/sud de la Thaïlande) — non demandé, complexité inutile pour l'usage
  actuel.
- Pays au climat hétérogène (USA, Indonésie, Brésil, Australie, Chine, Inde) —
  restent sur la saisie par ville, pas de mapping pays forcé.
