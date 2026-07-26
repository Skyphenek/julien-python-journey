# Terminal Mac (zsh, AZERTY FR) — cheatsheet complète débutant

Tout ce qu'il te faut pour survivre puis être efficace dans le terminal, avec les raccourcis AZERTY spécifiques (les caractères casse-tête : `|`, `~`, `\`, `{`, `}`, `[`, `]`).

Ton terminal par défaut sur Mac : **zsh** (pas bash). Certaines commandes bash marchent, mais quelques subtilités changent (ex : `.zshrc` au lieu de `.bashrc`).

---

## 0. Ouvrir le terminal

- **Terminal.app** : Cmd + Espace → tape "terminal"
- **Terminal Cursor** : `Ctrl + backtick` (Ctrl + la touche `` ` `` sous Échap)
- **Débloquer** si tu vois `dquote>` / `subsh>` / `>` (guillemet non fermé) : **Ctrl + C**

---

## 1. Les caractères AZERTY qui coincent (à graver)

| Caractère | Raccourci Mac AZERTY | Sert à |
|---|---|---|
| `\|` (pipe) | **Option + Shift + L** | chaîner deux commandes |
| `~` (tilde) | **Option + N** | ton home (`~` = `/Users/julien`) |
| `\` (backslash) | **Option + Shift + /** | échapper un caractère |
| `{` `}` | **Option + (** et **Option + )** | blocs Python/JS |
| `[` `]` | **Option + Shift + (** et **Option + Shift + )** | listes, index |
| `#` | **Option + Shift + 3** | commentaire, ID Git |
| `` ` `` (backtick) | Sous la touche Échap (à gauche du 1) | ancien shell exec |
| `@` | **Option + 0** (parfois direct) | emails, décorateurs Python |
| `€` | **Option + $** | euro |

**Astuce** : quand tu n'arrives pas à taper un caractère, essaie `Option + shift` + le caractère qui lui ressemble sur le clavier.

### ⚠️ Piège Cursor : Option ne produit pas `{` `}` dans le terminal

**Symptôme** : `Option + 5` fait `{` dans TextEdit / Chrome / partout, **sauf dans le terminal Cursor** où rien ne s'affiche.

**Cause** : par défaut, Cursor (et VS Code) traite Option comme touche **Meta** dans le terminal intégré. Ça bouffe les caractères spéciaux AZERTY.

**Fix (une fois pour toutes)** :

1. **Cmd + ,** (ouvre Settings)
2. Cherche `macOptionIsMeta`
3. **Décoche** `Terminal › Integrated: Mac Option Is Meta` (ou passe à `false`)
4. Ouvre un nouveau terminal (`Ctrl + backtick`) pour appliquer

Ou directement dans `settings.json` :
```json
"terminal.integrated.macOptionIsMeta": false
```

**Même piège sur Terminal.app** : Réglages → Profils → Clavier → décoche "Utiliser la touche Option comme touche Meta".

**Même piège sur iTerm2** : Settings → Profiles → Keys → Left Option Key = **Normal** (pas Meta).

---

## 2. Navigation — où suis-je, où je vais

```bash
pwd                     # print working directory : où suis-je ?
ls                      # list : ce qu'il y a ici
ls -l                   # détails (taille, date, permissions)
ls -la                  # + fichiers cachés (commencent par .)
ls -lh                  # tailles lisibles (Ko, Mo)
cd dossier              # entrer dans "dossier"
cd ..                   # remonter d'un niveau
cd                      # revenir au home (~)
cd -                    # revenir au dossier précédent
cd ~/Claude/Work        # aller directement à ce chemin
```

**Notation de chemin** :
- `.` = dossier actuel
- `..` = dossier parent
- `~` = ton home (`/Users/julien`)
- `/` = racine du disque

**Piège** : les chemins sont **case-sensitive** sur Linux, **case-insensitive** par défaut sur Mac (mais mieux vaut respecter la casse).

---

## 3. Fichiers et dossiers — créer, copier, supprimer

```bash
touch fichier.txt              # crée un fichier vide
mkdir mon_dossier              # crée un dossier
mkdir -p a/b/c                 # crée toute l'arbo si besoin

cp source dest                 # copie
cp -r dossier1 dossier2        # copie récursive (dossier)

mv source dest                 # déplace OU renomme
mv fichier.txt archive.txt     # renomme

rm fichier.txt                 # SUPPRIME (pas de corbeille)
rm -r mon_dossier              # supprime dossier + contenu
rm -rf mon_dossier             # force sans confirmation ⚠️
```

**⚠️ Piège mortel** : `rm -rf /` = tu détruis ton Mac. Ne JAMAIS lancer `rm -rf` sans lire deux fois le chemin.

---

## 4. Lire un fichier

```bash
cat fichier.txt                # affiche tout d'un coup
less fichier.txt               # affiche avec pagination (q pour quitter)
head fichier.txt               # 10 premières lignes
head -n 20 fichier.txt         # 20 premières lignes
tail fichier.txt               # 10 dernières lignes
tail -f log.txt                # suit un fichier qui grossit (logs)
wc -l fichier.txt              # nombre de lignes
```

**Sortir de `less`** : appuie sur `q`.

---

## 5. Rechercher

### Chercher un fichier par nom
```bash
find . -name "*.py"                # tous les .py dans le dossier actuel + sous-dossiers
find ~/Claude -name "concepts*"    # tous les fichiers dont le nom commence par "concepts"
find . -type d -name "session*"    # dossiers seulement
```

### Chercher dans le contenu des fichiers
```bash
grep "erreur" log.txt              # les lignes qui contiennent "erreur"
grep -i "erreur" log.txt           # insensible à la casse
grep -r "def frais" .              # récursif dans tous les fichiers
grep -n "erreur" log.txt           # affiche numéro de ligne
grep -v "OK" log.txt               # inverse (lignes qui ne contiennent PAS "OK")
```

### Combo puissant
```bash
find . -name "*.py" | xargs grep "montant"    # cherche "montant" dans tous les .py
```

---

## 6. Redirections et pipes

```bash
commande > fichier.txt         # écrit la sortie DANS le fichier (écrase)
commande >> fichier.txt        # ajoute à la fin
commande < fichier.txt         # utilise le fichier comme entrée
commande1 | commande2          # sortie de 1 = entrée de 2
```

**Exemples pratiques** :
```bash
ls -la > listing.txt                    # sauvegarde le listing
cat log.txt | grep "ERROR" | wc -l      # compte les erreurs dans un log
python3 script.py > output.txt          # capture le print() dans un fichier
python3 script.py 2> erreurs.txt        # capture les erreurs (stderr)
python3 script.py > out.txt 2>&1        # capture tout (stdout + stderr)
```

---

## 7. Édition rapide d'un fichier

### `nano` — le plus simple pour débuter
```bash
nano fichier.txt
```
- Édite normalement
- **Ctrl + O** : sauvegarder (write out) — Entrée pour confirmer
- **Ctrl + X** : quitter
- **Ctrl + K** : couper une ligne
- **Ctrl + W** : chercher

### `vim` — à connaître minimum (tu tomberas dedans un jour)
```bash
vim fichier.txt
```
- Par défaut en **mode commande** : tu ne peux PAS taper
- `i` : passer en mode insertion (là tu peux taper)
- `Échap` : revenir en mode commande
- `:w` + Entrée : sauvegarder
- `:q` + Entrée : quitter
- `:wq` + Entrée : sauvegarder + quitter
- `:q!` + Entrée : quitter SANS sauvegarder (si tu es coincé)

**Si tu es coincé dans vim** : Échap, puis tape `:q!` puis Entrée. Ça sort sans rien sauvegarder.

---

## 8. Raccourcis clavier zsh (indispensables)

| Raccourci | Effet |
|---|---|
| **Ctrl + C** | interrompt la commande en cours |
| **Ctrl + D** | ferme le terminal / envoie EOF |
| **Ctrl + L** | efface l'écran (comme `clear`) |
| **Ctrl + A** | début de ligne |
| **Ctrl + E** | fin de ligne |
| **Ctrl + U** | efface tout à gauche du curseur |
| **Ctrl + K** | efface tout à droite |
| **Ctrl + W** | efface le mot précédent |
| **Ctrl + R** | recherche dans l'historique (retape et Ctrl+R pour cycler) |
| **↑ / ↓** | commande précédente / suivante |
| **Tab** | autocomplète nom de fichier / commande |
| **Tab Tab** | affiche les possibilités si ambigu |

**Ctrl + R** est le raccourci qui change la vie : tu tapes 3 lettres, il retrouve la commande dans ton historique.

---

## 9. Historique

```bash
history                        # toutes les commandes précédentes
history | grep git             # celles qui contiennent "git"
!123                           # relance la commande n°123 de l'historique
!!                             # relance la commande précédente
sudo !!                        # relance la précédente en sudo
```

---

## 10. Permissions et sudo

```bash
ls -l                          # affiche les permissions (rwx)
chmod +x script.sh             # rend un fichier exécutable
chmod 755 script.sh            # permissions numériques (avancé)
sudo commande                  # exécute en tant qu'admin (mot de passe demandé)
```

**Règle** : ne mets JAMAIS `sudo` sans réfléchir. Si tu ne sais pas pourquoi une commande le demande, cherche avant.

---

## 11. Processus

```bash
ps                             # tes processus
ps aux                         # TOUS les processus
top                            # vue live des processus (q pour quitter)
htop                           # version moderne de top (à installer via brew)
kill 1234                      # tue le processus PID 1234 (poliment)
kill -9 1234                   # tue de force
pkill -f "python"              # tue tous les processus qui matchent "python"
```

**Cas typique** : ton script Python tourne dans le vide → Ctrl + C. Ne marche pas → nouveau terminal, `ps aux | grep python`, puis `kill <PID>`.

---

## 12. Réseau — les 3 commandes utiles

```bash
ping google.com                # teste ta connexion
curl https://api.example.com   # récupère une URL (GET)
curl -X POST -d "data" URL     # POST avec données
wget https://example.com/f.pdf # télécharge un fichier
```

**Sortir de `ping`** : Ctrl + C.

---

## 13. Variables d'environnement

```bash
echo $HOME                     # affiche la valeur de HOME
echo $PATH                     # les chemins où le shell cherche les commandes
export MA_VAR="valeur"         # crée une variable pour la session
env                            # toutes les variables actuelles
```

**Rendre une variable permanente** : l'ajouter dans `~/.zshrc` :
```bash
echo 'export MA_VAR="valeur"' >> ~/.zshrc
source ~/.zshrc                # recharge le fichier
```

---

## 14. Aliases — tes raccourcis persos

Édite `~/.zshrc` :
```bash
alias ll="ls -la"
alias gs="git status"
alias claude="cd ~/Claude"
alias venv="source .venv/bin/activate"
```

Puis :
```bash
source ~/.zshrc                # recharge
```

Maintenant tu tapes `ll` au lieu de `ls -la`.

---

## 15. Python dans le terminal

```bash
python3                        # ouvre l'interpréteur (Ctrl+D pour sortir)
python3 script.py              # lance un script
python3 -m module              # lance un module
python3 -c "print(2+2)"        # exécute une ligne

pip install requests           # installe un package
pip install -r requirements.txt # installe depuis un fichier
pip list                       # liste installés
pip show requests              # infos sur un package
```

### Environnement virtuel
```bash
python3 -m venv .venv          # crée l'env dans .venv/
source .venv/bin/activate      # ACTIVE l'env (indispensable)
# ton prompt affiche maintenant (.venv)
pip install pandas             # installé UNIQUEMENT dans cet env
deactivate                     # sortir de l'env
```

**Règle** : un projet = un venv. Sinon tu vas mélanger les versions.

---

## 16. Git — les 15 commandes qui couvrent 95% des cas

```bash
git status                     # où j'en suis
git add fichier                # marque un fichier prêt à committer
git add .                      # tous les changements
git commit -m "message"        # crée un commit
git log                        # historique (q pour quitter)
git log --oneline              # historique condensé

git diff                       # ce que tu as modifié mais pas ajouté
git diff --staged              # ce qui est prêt à committer

git branch                     # branches locales
git checkout -b ma_branche     # crée + bascule sur nouvelle branche
git checkout main              # revient sur main

git pull                       # récupère du serveur distant
git push                       # envoie vers le distant
git push -u origin ma_branche  # 1re fois qu'on pousse une branche

git clone URL                  # récupère un repo
```

**Piège AZERTY** : `git commit -m "message"` — les guillemets `"` sont **Option + Shift + 3** ? Non — `"` est direct sur AZERTY (touche 3). Vérifie ce que tu tapes vraiment.

---

## 17. Homebrew — le gestionnaire de packages Mac

Installation (à faire une fois) :
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Puis :
```bash
brew install htop              # installe un outil
brew install --cask cursor     # installe une app graphique
brew update                    # met à jour la liste
brew upgrade                   # met à jour les outils installés
brew list                      # ce que tu as installé
brew search python             # cherche un package
```

---

## 18. Astuces zsh spécifiques

### Autocomplétion Tab
- Tape 3 lettres + Tab → complète si non ambigu
- Tape + Tab Tab → affiche les possibilités
- Marche pour commandes, fichiers, options, branches git

### Expansion de chemin
```bash
ls ~/Cla<Tab>                  # complète en ~/Claude/
cd **/*.py                     # glob récursif (zsh only)
```

### Répéter une partie de commande précédente
```bash
!$                             # dernier argument de la commande précédente
                               # ex: mkdir long/path → cd !$
```

### Redémarrer une commande longue en arrière-plan
```bash
python3 long_script.py &       # tourne en tâche de fond
jobs                           # liste les jobs
fg                             # ramène au premier plan
```

---

## 19. Cas d'usage typiques (à connaître par cœur)

### "Je veux voir combien de lignes dans mon CSV"
```bash
wc -l data.csv
```

### "Je veux voir les 5 premières lignes"
```bash
head -n 5 data.csv
```

### "Je veux compter les fichiers Python dans un dossier"
```bash
find . -name "*.py" | wc -l
```

### "Je veux chercher toutes les fonctions qui contiennent 'frais'"
```bash
grep -rn "def.*frais" .
```

### "Je veux copier un fichier en gardant l'original"
```bash
cp fichier.py fichier.py.backup
```

### "Je veux archiver un dossier en .zip"
```bash
zip -r archive.zip mon_dossier
```

### "Je veux voir la taille d'un dossier"
```bash
du -sh mon_dossier
```

### "Je veux voir l'espace disque restant"
```bash
df -h
```

### "Je suis perdu dans une commande — comment sortir ?"
- Prompt bizarre (`>`, `dquote>`, `heredoc>`) → **Ctrl + C**
- Script bloqué → **Ctrl + C**
- Coincé dans `less` / `man` / `top` → **q**
- Coincé dans `vim` → **Échap** puis `:q!` puis Entrée

---

## 20. Les 10 pièges du débutant Mac AZERTY

1. **Guillemets manquants** → prompt affiche `dquote>`. Solution : **Ctrl + C**.
2. **Pipe `|` introuvable** → **Option + Shift + L**. Écris-le sur un post-it au début.
3. **`~` non tapé** → **Option + N**.
4. **Espaces dans les noms de dossier** → toujours guillemets :
   ```bash
   cd "~/Claude/Work/Legal Requests"
   ```
5. **Case-sensitive parfois** → `Cd` ne marche pas, `cd` oui.
6. **Coller un chemin depuis Finder** → glisse le dossier depuis Finder dans le terminal, le chemin s'écrit tout seul.
7. **Confondre `~` et `/`** → `~` = home, `/` = racine du disque. Deux choses différentes.
8. **Oublier `python3`** → sur Mac récent, `python` peut ne pas exister. Toujours `python3`.
9. **Oublier `source .venv/bin/activate`** avant `pip install` → tu installes globalement au lieu du projet.
10. **Utiliser `rm`** au lieu de la corbeille → pas de retour possible. Pour sécuriser :
    ```bash
    alias rm="rm -i"           # demande confirmation
    ```

---

## 21. Man et help — quand tu ne sais plus

```bash
man ls                         # documentation complète de ls (q pour sortir)
ls --help                      # aide rapide (marche sur la plupart des commandes)
which python3                  # où se trouve la commande ?
type ls                        # est-ce un alias / builtin / fichier ?
```

---

## 22. Ce qui doit devenir automatique

- **Ctrl + C** dès qu'un truc part en vrille
- **Ctrl + R** au lieu de retaper une longue commande
- **Tab** pour compléter, toujours
- **`pwd`** dès que tu as un doute sur où tu es
- **Option + Shift + L** pour `|` (mémoire musculaire à construire)
- **Option + N** pour `~`
- **`source .venv/bin/activate`** avant tout `pip` ou `python3`
- **Guillemets** autour de tout chemin qui contient un espace
- **Toujours relire un `rm -rf`** avant de valider

---

## Récap ultra-condensé

```
NAVIGATION
pwd                  où suis-je
ls -la               tout voir
cd dossier           entrer
cd ..                remonter
cd ~                 home

FICHIERS
touch f              créer
mkdir -p a/b         créer arbo
cp src dst           copier
mv src dst           déplacer/renommer
rm f                 supprimer (⚠️)
cat f                lire
head/tail f          début/fin
less f               pager (q pour sortir)

RECHERCHE
find . -name "*.py"        par nom
grep -rn "texte" .         dans le contenu

REDIRECTION
> fichier            écrit
>> fichier           ajoute
|                    chaîne

RACCOURCIS
Ctrl+C               stop
Ctrl+L               clear
Ctrl+R               chercher historique
Tab                  compléter
↑                    précédente

PYTHON
python3 script.py
python3 -m venv .venv
source .venv/bin/activate
pip install <pkg>

GIT
git status / add . / commit -m "..." / push
git pull / log --oneline
git checkout -b branche

AZERTY MAC
| = Option+Shift+L
~ = Option+N
\ = Option+Shift+/
{ } = Option+( Option+)
[ ] = Option+Shift+( Option+Shift+)
# = Option+Shift+3
```

---

## Où tu vas revoir tout ça

- **Chaque session Python** : tu tapes du terminal dès `python3 script.py`.
- **Chaque commit** : `git add / commit / push`. Séquence à mémoriser.
- **Cursor** : le terminal intégré est le même zsh que Terminal.app. Tous ces raccourcis marchent identiquement.
- **Quand tu bloques 30 secondes** : ctrl+F sur cette fiche AVANT d'aller sur Google.
