---
titre: JS 01 — Modèle mental (page qui réagit) — zone augmentée
date: 2026-08-04
parcours: js (zone augmentée — lecture/compréhension, pas écriture from scratch)
source: ~/Claude/Work/perso/python/julien-python-journey/voyage/valise.py (constante HTML_SCRIPT)
---

> **À quoi sert cette fiche** : comprendre ce que fait le JavaScript de ta checklist valise, sans avoir à l'écrire toi-même. C'est ta zone *augmentée* : tu pilotes le Python, le JS je te le livre, toi tu dois juste savoir lire ce qui se passe.

Tous les exemples viennent de `valise.py` (page générée).

---

## 1. Le grand principe : Python fige, JS réagit

| | Python (ton moteur) | JavaScript (dans la page) |
|---|---|---|
| Où ça tourne | dans le terminal, **une fois** | dans le navigateur, **en continu** |
| Ce que ça produit | un fichier HTML **figé** | une page qui **réagit** (clics, coches) |
| Analogie | imprimer un formulaire | le formulaire qui te répond quand tu écris dessus |

Le JS est injecté dans la page (`<script>...</script>`) par ton Python. Une fois la page ouverte, Python est parti ; c'est le JS qui vit.

---

## 2. Attraper un élément, puis le changer

Le JS agit en deux temps : **trouver** un morceau de la page, puis le **modifier**.

```javascript
document.getElementById('compte')          // trouve l'élément dont id="compte"
document.querySelectorAll('input[type=checkbox]')  // trouve TOUTES les cases
```
- `document` = la page entière.
- `getElementById` = un seul élément (par son id unique). `querySelectorAll` = une liste (par un motif CSS).

Une fois attrapé, on le modifie :
```javascript
element.textContent = "3 / 18";        // changer son texte
element.style.display = 'none';        // le cacher (display:none = retiré de l'affichage)
box.checked = true;                    // cocher une case
b.classList.toggle('actif', vrai);     // ajouter/retirer une classe CSS
```

**Ancrage** : c'est ton `SELECT` (trouver) puis `UPDATE` (modifier), mais sur des éléments de page.

---

## 3. Écouter un événement

"Quand X arrive, fais Y." Le cœur de l'interactivité.

```javascript
box.addEventListener('change', function () {
    // ... ce qui se passe quand on coche/décoche cette case
});
```
- `'change'` = la case a changé d'état ; `'click'` = on a cliqué un bouton.
- La fonction entre `{ }` est **mise en réserve** : elle ne s'exécute pas tout de suite, seulement quand l'événement arrive.

Dans ta valise : chaque case a un écouteur `change` qui sauvegarde + met à jour la barre et les compteurs.

---

## 4. State → render (le pattern central)

Idée : garder un **petit état** en mémoire, et des **fonctions qui redessinent** la page à partir de cet état. On ne bricole jamais la page à la main ; on change l'état, puis on redessine.

Dans ta valise, l'état tient en 2 variables :
```javascript
let ownerActif = null;   // quelle personne est affichée
let masquer = false;     // masque-t-on les objets rangés ?
```
Et les "fonctions qui redessinent" : `majProgression()`, `majOnglets()`, `appliquerMasque()`, `activer()`.

Le cycle : un clic **change l'état** (ex. `masquer = !masquer`) → on **rappelle les fonctions** → la page reflète le nouvel état. C'est exactement le principe de React/Vue, en version artisanale.

---

## 5. localStorage : la mémoire du navigateur

Un tiroir clé→valeur qui **survit au reload** et à la fermeture de l'onglet.

```javascript
localStorage.setItem(CLE, JSON.stringify(sauvegarde));  // écrire (UPSERT)
JSON.parse(localStorage.getItem(CLE) || "{}");          // lire (SELECT)
```
- `setItem/getItem` = écrire / lire une valeur sous une clé.
- Le tiroir ne stocke que du **texte** : `JSON.stringify` transforme ton objet en texte pour le ranger, `JSON.parse` fait l'inverse à la relecture.

**Ancrage** : une mini-table clé→valeur locale au navigateur. Elle est **par appareil** (laptop ≠ téléphone).

**Piège vécu** : au départ la clé du tiroir dépendait du titre de la page ; sur des fichiers `file://` la séparation n'a pas tenu, les objets communs à deux voyages partageaient leur coche. **Fix** : graver la destination dans la clé de CHAQUE objet (`data-key="Italie/Julien/..."`) → collision impossible. Une clé unique et explicite bat un contexte implicite (comme tes clés de dict Python).

---

## 6. "Recalculer, pas stocker"

La barre de progression et les compteurs d'onglets ne sont **jamais stockés**. À chaque changement, on **recompte** depuis l'état des cases :

```javascript
let faites = 0;
boxes.forEach(function (b) { if (b.checked) faites++; });   // COUNT(*) WHERE cochée
```

**Ancrage** : c'est un agrégat SQL relancé en direct. Le total n'est qu'une **vue** de l'état courant, pas une donnée à maintenir. Moins de choses à synchroniser = moins de bugs.

---

## À retenir

- Tu n'as pas besoin d'écrire ce JS. Tu dois savoir **lire le comportement** : trouver un élément → le modifier ; écouter un événement → réagir ; changer l'état → redessiner.
- Les 3 idées transférables (partout, pas que ici) : **state→render**, **localStorage** (persistance sans base), **recalculer plutôt que stocker**.
- Le reste (syntaxe `function`, `forEach`, `=>`) : tu le reconnais grâce à Jiki, mais ce n'est pas ton terrain d'écriture. Voir [[python-03-html-fichiers-sets-2026-07-29]] pour la partie que tu maîtrises (générer le HTML côté Python).
