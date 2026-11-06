---
name: chef-casa
description: Améliore en place les recettes du hub Casa Binomerie (table plats dans Neon) — trucs de chef, gestes précis, secrets de grand-mère de Julien — pour qu'un plat « correct » devienne « vraiment bon ». Déclencher quand Julien veut améliorer, enrichir ou « passer au chef » une ou plusieurs recettes de la Casa, ou revient après avoir cuisiné une recette améliorée. Ne pas déclencher pour ajouter une recette, changer un ingrédient, un temps ou les portions.
---

# Chef de la Casa

But : le « petit truc qui fait la différence », écrit dans la recette elle-même, lisible sur l'iPhone en cuisine.
Commande (depuis n'importe quel dossier) : CHEF = `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py`
Spec : `~/Claude/Work/perso/python/julien-python-journey/docs/superpowers/specs/2026-11-06-casa-chef-design.md`.

## Déroulé d'une session (5 recettes au plus)

1. `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py file` : montre les 5 prochaines (colonne 1 = fois cuisinée). Julien garde, retire, ou
   impose une recette (`~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py lire <id>` directement).
2. Pour chaque recette, une à la fois :
   a. `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py lire <id>` ; garder `maj_le`.
   b. Demander : « Tu as un truc à toi sur ce plat ? » — attendre la réponse avant de rédiger.
   c. Rédiger la nouvelle version selon les règles ci-dessous. Montrer : l'ancienne version des étapes touchées, puis la
      recette complète proposée (bloc de code), puis « Ce que j'ai changé et pourquoi » (puces courtes), puis ce qui
      est signalé sans être corrigé.
   d. Attendre un OK explicite. Une correction de Julien → nouvelle version complète, nouvel OK.
   e. Écrire le texte validé dans un fichier du scratchpad, puis
      `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py ecrire <id> <fichier> --maj <maj_le>`. Code 3 : la recette a bougé dans l'app →
      relire, refaire la proposition sur la nouvelle version. Jamais de SQL à la main.
      Code 1 ou 2 : erreur (id, fichier, bloc final, `--maj` sans fuseau) → la montrer à Julien, ne pas relire en boucle.
3. En fin de session : ajouter dans `~/Claude/TASKS.md` une tâche « Cuisiner <recettes> version chef et dire ce qui
   a fait la différence ».

## Retour après cuisson

Julien dit ce qui a marché ou non → `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py lire <id>`, retirer le geste inutile, renforcer celui qui a marché,
même circuit (proposition, OK, `ecrire`). Un truc de Julien découvert en cuisinant entre en *secret de grand-mère*.

Mesure du succès : sur les 5 premières recettes passées et cuisinées, au moins 4 ont « fait la différence » selon
Julien ; sinon, revoir ces règles avant de continuer.

## Règles de rédaction

1. **Les secrets de Julien d'abord.** Marqués « (secret de grand-mère : … ) » dans l'étape concernée. Ils priment
   sur toute proposition de Claude qui les contredit. « Secret de grand-mère » est réservé aux trucs de Julien ;
   « secret de mamma » reste la convention des recettes Mamma déjà en base.
2. **2 à 4 trucs, pas plus** : assaisonnement (acide, sel au bon moment, finition), technique (saisie, réduction,
   repos, monter au beurre), ingrédient qui change tout (de préférence déjà au placard), texture et dressage.
   Un truc qui n'améliore pas nettement le résultat n'est pas proposé. Pas de débat d'école : si la version
   actuelle marche, on la garde.
3. **Test du geste** — chaque verbe d'action répond à :
   - avec quoi (spatule en bois, plat de casserole, doigts) ;
   - dans quel sens / comment (à plat comme une épingle, du centre vers les bords) ;
   - jusqu'à quel signal vu, entendu ou senti (le beurre mousse et chante, l'alcool ne pique plus le nez).
   Un temps en minutes seul ne suffit pas : il accompagne le signal.
4. **Le pourquoi dans la même phrase**, entre tirets : « — humide, la viande bout au lieu de dorer ».
5. **L'ordre suit les gestes** : si deux gestes se contredisent (eau pour aplatir / viande sèche pour dorer),
   réordonner (aplatir, puis sécher) et le dire dans l'étape.
6. **Ne bouge pas** : la liste d'ingrédients (seule une répartition : « dont 30 g froid »), les temps, les
   portions. Les « jamais » de Laetitia restent dehors (`~/brain/bin/brain recall "Laetitia goûts jamais"`).
7. **Signaler sans corriger** le hors-sujet (« Pour 4 » alors qu'on est deux) : dans la proposition, pas dans la
   recette.
8. **Bloc final obligatoire**, dernière section du texte, 3 lignes au plus :
   ```
   Ce qui fait la différence
   - <truc> : <effet dans l'assiette>.
   ```
   Un ancien bloc « Erreurs fréquentes » est absorbé par les étapes et ce bloc.
9. **Ton** : tutoiement, phrases courtes, comme les recettes existantes. Format conservé : « Pour N », liste
   d'ingrédients en tirets, étapes numérotées.

## Exemple de référence : `plat-saltimbocca` (écrit le 06/11/2026)

Étape avant : « Monter les saltimbocca : sur chaque escalope, pose 1 tranche de prosciutto, puis 1 feuille de
sauge. Fixe avec 1 cure-dent (ou une petite pique) pour que tout tienne à la cuisson. »

Étape après : « Monter les saltimbocca : pose le prosciutto sur l'escalope, ce qui dépasse replié dessous, puis la
sauge au centre, face brillante vers le haut. Pique le cure-dent à plat, comme une épingle de couturière : il entre
à côté de la sauge, traverse feuille, jambon et veau, et ressort par le dessus 2 cm plus loin (secret de mamma :
piqué droit, il fait basculer l'escalope dans la poêle ; à plat, elle reste collée au fond et dore partout). »

Secret de grand-mère de Julien (étape 1) : quelques gouttes d'eau sur le veau entre les films avant d'aplatir —
l'eau fait roulement à billes, la viande s'étale au lieu de se déchirer ; puis sécher avant de saler.

Version complète : `~/Claude/Work/perso/python/julien-python-journey/voyage/.venv/bin/python ~/Claude/Work/perso/python/julien-python-journey/voyage/chef.py lire plat-saltimbocca`.

## Limites à dire

Les trucs de Claude sont de la technique classique, pas des secrets de famille vérifiés : le retour de Julien après
cuisson décide. Si le skill ne connaît pas un plat (régional, familial), il le dit et pose plus de questions.

L'app n'a pas de verrou : une fiche restée ouverte sur un téléphone avec l'ancien texte, enregistrée après le passage
du chef, écrase la version chef sans prévenir. Garder le texte validé dans le scratchpad jusqu'à la fin de la session ;
prévenir Laetitia de recharger la recette.
