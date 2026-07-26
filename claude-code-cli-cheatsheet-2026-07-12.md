# Claude Code CLI — cheatsheet complète

Fiche de référence pour exploiter Claude Code au max, calquée sur ton style Python/terminal. Ordre : du modèle mental → aux commandes du quotidien → aux leviers avancés.

**Ancrage** : je te donne l'équivalent SQL / Notion / n8n entre parenthèses quand c'est pertinent, et je pointe systématiquement vers **tes** fichiers (JULIEN.md, brain, STATUS.md, TASKS.md).

---

## 1. Le modèle mental (à graver avant tout)

**Claude Code n'est pas un chatbot.** C'est un **harness** : un runtime qui pilote un modèle (Opus/Sonnet/Haiku) avec des outils (Read, Edit, Bash, WebFetch, Task…) sur ton système de fichiers.

Trois couches à distinguer en permanence :

| Couche | Qui la contrôle | Exemple |
|---|---|---|
| **Modèle** | Anthropic | Opus 4.7, Sonnet 4.6, Haiku 4.5 |
| **Harness** | Le CLI + `settings.json` | Hooks, permissions, MCP, skills |
| **Contexte** | Toi (fichiers CLAUDE.md, @refs, mémoire) | JULIEN.md, brain, STATUS.md |

**Conséquence directe** : une automatisation *"à chaque fois que X, fais Y"* n'appartient pas à la mémoire ou à un CLAUDE.md — c'est un **hook** dans `settings.json`. Le modèle ne peut pas la fulfiller tout seul.

**Piège** : demander au modèle de "se souvenir toujours de X" alors que X est un déclencheur automatique. Réponse : `/update-config` (skill) pour poser le hook.

---

## 2. Ouvrir, naviguer, quitter

### Ouvrir le CLI depuis le bon dossier
```bash
cd ~/Claude/Work/automation/Legal\ Requests/
claude
```
Le dossier d'ouverture détermine **quels CLAUDE.md se chargent** (voir §14). Ouvrir depuis la racine `~/` = uniquement config globale.

### Reprendre une session
```bash
claude --resume           # menu de sessions récentes
claude --continue         # reprend la toute dernière
claude -c                 # alias de --continue
```

### Quitter proprement
- `Ctrl + D` (EOF) → sortie propre
- `/exit` → idem
- `Ctrl + C` deux fois → interrompt puis quitte

### Contrôles interactifs (à automatiser dans les doigts)

| Raccourci | Effet |
|---|---|
| **Enter** | envoyer le message |
| **Shift + Enter** | saut de ligne (garde le curseur) |
| **Ctrl + C** | interrompt l'action en cours (le tool call) |
| **Escape** | interrompt le modèle **pendant qu'il génère** |
| **Escape × 2** | rejeter tout jusqu'au dernier tour user (rollback léger) |
| **↑ / ↓** | historique des prompts |
| **Tab** | complète les chemins de fichiers |
| **Ctrl + R** | recherche inversée dans l'historique (comme zsh) |

**Piège** : `Ctrl + C` pendant génération = coupe SA sortie, tu perds la fin. Pour juste "l'arrêter", utilise Escape.

---

## 3. Modèles : Opus / Sonnet / Haiku + fast mode

Ta règle globale (JULIEN.md) : **Haiku par défaut, flag proactif quand ça dépasse**. Sonnet 4.6 = milieu de gamme. Opus 4.7 = raisonnement complexe / coup dur.

### Changer de modèle
```
/model                    # menu interactif
/model haiku              # switch immédiat
/model sonnet
/model opus
```

### Fast mode (Opus 4.6 accéléré)
```
/fast                     # toggle on/off
```
Opus 4.6 avec sortie plus rapide, pas de downgrade en Haiku sous le capot. Utile pour Opus en itération dense.

### Décider quel modèle
| Situation | Modèle |
|---|---|
| Question factuelle, lookup, edit ciblé | **Haiku** |
| Refactor multi-fichiers, review, écriture d'un draft moyen | **Sonnet** |
| Design système, arbre de décision, prompt complexe, analyse ambigüe | **Opus** |
| Trop lent en Opus mais besoin du niveau | **`/fast`** |

**Piège** : rester en Opus par flemme = brûle du budget + du cache. Si tu poses une question simple à Opus, switch Haiku.

---

## 4. @-mentions : injecter des fichiers dans le contexte

Le `@` inline ajoute le contenu du fichier au message envoyé au modèle (comme un `cat` implicite, mais compté dans les tokens).

```
Regarde @src/analyseur.py et dis-moi ce qui coince
Compare @STATUS.md avec @../automation/STATUS.md
```

- **Autocomplete** : tape `@` puis les premières lettres → Tab pour compléter
- Fonctionne aussi sur des dossiers (résume l'arbo)
- **N'inclut PAS** les fichiers cachés (`.git/`, `.env`) par défaut

**Piège** : `@` un gros fichier (>1000 lignes) = burn de cache. Préfère demander au modèle de le lire avec Read (il ne lit que ce qu'il lui faut).

---

## 5. `!` prefix : bash inline

Un message qui commence par `!` s'exécute **dans ton shell**, pas envoyé au modèle. Le stdout atterrit directement dans la conversation, visible par le modèle au tour suivant.

```
!ls -la ~/Claude/Work/automation/
!git log --oneline -5
!~/brain/bin/brain recall "harness krone"
!gcloud auth login          # exécution interactive dans TA session
```

**Cas d'or** : login interactif (`gcloud`, `gh auth`, `az login`) — tu tapes le browser flow toi-même, la sortie revient dans la session.

**Piège** : `!rm -rf` s'exécute réellement. Pas de garde-fou. Vérifie deux fois.

---

## 6. Slash commands built-in

Les commandes du harness. Elles ne consomment pas de tokens (sauf celles qui appellent un skill).

| Commande | Effet |
|---|---|
| `/help` | liste des commandes du harness |
| `/clear` | vide le contexte (nouveau départ, mémoire préservée) |
| `/compact` | résume le contexte pour libérer de la place (garde le fil) |
| `/model` | menu de sélection de modèle |
| `/fast` | toggle fast mode |
| `/config` | ouvre l'UI de config (thème, model, notifs) |
| `/status` | montre le modèle actif, tokens utilisés, hooks chargés |
| `/cost` | coût de la session en cours |
| `/resume` | reprendre une session |
| `/exit` | quitter |
| `/mcp` | liste des MCP servers connectés |
| `/permissions` | voir/modifier les tools autorisés |
| `/agents` | lister les sous-agents disponibles |
| `/hooks` | inspecter les hooks configurés |

**`/clear` vs `/compact`** :
- `/clear` = repartir de zéro (utile en début de nouvelle tâche sans rapport)
- `/compact` = garder le fil mais compresser (utile en session longue)

---

## 7. Custom slash commands

Tes propres commandes vivent dans :
- `~/.claude/commands/` → globales (dispo partout)
- `<projet>/.claude/commands/` → projet uniquement

### Structure d'une command

Un fichier `.md` avec frontmatter YAML :

```markdown
---
description: "Génère le brief matinal Julien"
argument-hint: "[date optionnelle]"
---

Tu es en mode brief matinal. Analyse :
- TASKS.md
- STATUS.md de chaque projet actif
- Événements du calendrier via MCP

Produis un brief en 3 sections : Priorités / Urgences / Nice-to-have.
Utilise l'argument date si fourni, sinon aujourd'hui.
```

### Voir ce que tu as
```bash
ls ~/.claude/commands/
```
Tu as déjà : `/brief`, `/todo`, `/log`, `/relance`, `/daily-tracker`, `/save`, `/consolidate-memory`, etc. (cf. ton CLAUDE.md global).

**Piège** : les commands sont juste des **prompts pré-écrits**. Une command ne peut pas déclencher une action automatique — pour ça, hook (§11).

---

## 8. Skills — capacités packagées

Les skills sont plus riches que les commands : elles ont un **trigger sémantique** (le modèle décide s'il faut les invoquer) et peuvent embarquer scripts + docs.

Emplacement : `~/.claude/skills/` (global) ou `.claude/skills/` (projet).

### Skills actifs sur ta machine (dernier check)

| Skill | Quand ça déclenche |
|---|---|
| `last30days` | recherche cross-source Reddit/X/YouTube/HN/etc. sur un topic récent |
| `capture-learning-session` | fin de session coaching → propose de consolider dans Learning Hub |
| `update-config` | modif de `settings.json` (permissions, hooks, env) |
| `keybindings-help` | rebind clavier `~/.claude/keybindings.json` |
| `simplify` | review du code changé (reuse, quality, efficiency) |
| `fewer-permission-prompts` | scan des transcripts → allowlist les tools répétitifs |
| `loop` | boucle un prompt / une command à intervalle |
| `schedule` | crée / gère des agents cron (triggers) |
| `claude-api` | build/debug/optimize d'app Anthropic SDK |
| `init` | initialise un `CLAUDE.md` dans un repo |
| `review` | review de PR |
| `security-review` | review sécurité du diff courant |

### Invoquer un skill
```
/last30days Claude Skills productivity
/simplify
/security-review
```

**Piège** : ne JAMAIS inventer un nom de skill de tête. Utilise la liste `available-skills` en début de session (ou `/help`). Un skill fantôme = tool call qui plante.

---

## 9. Sous-agents (Task tool)

Le modèle peut **déléguer** à un sous-agent isolé avec son propre contexte. Utile pour :
- Parallélisation
- Protéger le contexte principal d'une exploration massive
- Utiliser un agent spécialisé

### Sous-agents dispos sur ta machine

| Agent | Quand l'appeler |
|---|---|
| `Explore` | recherche codebase >3 queries (globs, greps, questions) |
| `Plan` | design de plan d'implémentation avant de coder |
| `general-purpose` | recherche multi-étapes, keyword sans confiance |
| `claude-code-guide` | question sur Claude Code / SDK / API Anthropic |
| `complexity-determinism-analyst` | extraction de règles déterministes d'un process flou (AML, LR DE) |
| `statusline-setup` | config de la statusline |

### Bien briefer un sous-agent

Un sous-agent n'a **PAS** le contexte de ta session. Le prompt doit être self-contained :
- objectif + contexte de fond
- ce que tu as déjà exclu
- format attendu ("under 200 words", liste, table)
- fichiers/lignes précises si tu en connais

**Piège** : `"based on your findings, fix the bug"` = tu délègues la compréhension. Fais l'analyse toi-même, donne l'edit précis à faire à l'agent.

**Parallélisation** : lance plusieurs agents dans **un seul message** = un seul aller-retour, exécution parallèle. Sinon séquentiel.

---

## 10. Hooks — automatisations qui ne dépendent pas du modèle

Un hook = commande shell exécutée par le harness à un événement. **C'est la seule façon** d'imposer un comportement automatique.

### Événements disponibles

| Event | Quand |
|---|---|
| `SessionStart` | au lancement de la session |
| `UserPromptSubmit` | à chaque prompt envoyé |
| `PreToolUse` | avant chaque tool call |
| `PostToolUse` | après chaque tool call |
| `Stop` | quand le modèle a fini un tour |
| `PreCompact` | avant `/compact` |

### Emplacement
`~/.claude/settings.json` (global) ou `<projet>/.claude/settings.json` (projet).

### Exemple : notifier quand Claude s'arrête
```json
{
  "hooks": {
    "Stop": [
      { "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" }
    ]
  }
}
```

### Exemple : lint auto sur les fichiers Python modifiés
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": { "tool_name": "Edit", "file_paths": ["*.py"] },
        "type": "command",
        "command": "ruff check $CLAUDE_TOOL_INPUT_file_path"
      }
    ]
  }
}
```

**Piège** : un hook qui échoue peut bloquer une action (PreToolUse retourne exit 1 → tool refusé). Test-le à part.

**Raccourci** : `/update-config` (skill) construit le JSON pour toi. Dis-lui *"chaque fois que Claude termine, joue un son"*.

---

## 11. Permissions et allowlist

Trois modes globaux :

| Mode | Comportement |
|---|---|
| **default** | prompt pour chaque tool sensible |
| **acceptEdits** | Edit/Write auto-approuvés, Bash reste demandé |
| **plan** | lecture seule, aucune modif |
| **bypassPermissions** | ⚠️ tout passe, à éviter sauf sandbox |

Changer : au lancement (`claude --permission-mode plan`) ou pendant la session (Shift+Tab cycle certains modes).

### Allowlist granulaire (dans `settings.json`)
```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(ls:*)",
      "Read(*)",
      "Grep(*)"
    ]
  }
}
```
Le pattern `Bash(git diff:*)` = tous les `git diff` autorisés. `Bash(rm:*)` = **jamais** l'écrire.

**Skill à utiliser** : `/fewer-permission-prompts` scanne tes transcripts et propose une allowlist priorisée. À lancer une fois de temps en temps.

**Piège** : `bypassPermissions` en prod = catastrophe. À réserver aux sandboxes jetables.

---

## 12. Fichiers de config — hiérarchie `settings.json`

Ordre de priorité (le plus spécifique gagne) :

```
1. .claude/settings.local.json  (projet, gitignored, priorité max)
2. .claude/settings.json         (projet, versionné)
3. ~/.claude/settings.json       (user global)
4. defaults harness
```

**Règle** : mets tes préférences perso dans `~/.claude/settings.json`, les règles projet (hooks CI, allowlist stricte) dans `<projet>/.claude/settings.json`, les overrides ponctuels dans `.local.json`.

Skill dédié : `/update-config`.

---

## 13. `CLAUDE.md` — hiérarchie du contexte

Chaque `CLAUDE.md` sur le chemin d'ouverture est chargé, **du plus général au plus spécifique** :

```
~/.claude/CLAUDE.md                             ← toi, global (JULIEN.md, life-context)
~/Claude/Work/CLAUDE.md                         ← workspace pro
~/Claude/Work/automation/CLAUDE.md              ← domaine automation
~/Claude/Work/automation/Legal Requests/CLAUDE.md ← projet LR DE
```

### Règle Julien (déjà appliquée dans ton setup)
- **Stable** dans CLAUDE.md (règles, conventions, adresses de fichiers)
- **Volatile** dans STATUS.md par domaine (état courant, dates, prochaines étapes)
- **Tâches** dans TASKS.md à la racine `~/Claude/`

### Références inline
Dans un CLAUDE.md tu peux faire :
```markdown
@/Users/julien/.claude/memory/JULIEN.md
```
= inclusion transitive au démarrage.

**Piège** : entasser du volatile dans un CLAUDE.md → le fichier grossit, le contexte se pollue, et tu oublies de le mettre à jour. Volatile = STATUS.md.

---

## 14. Mémoire persistante

Deux systèmes distincts sur ta machine :

### A. `~/brain/` — ton second brain déterministe
```bash
~/brain/bin/brain recall "la question"
~/brain/bin/brain remember --type domain --title "..." --keywords "a,b,c" --body "..."
~/brain/bin/brain push        # sync GitHub
~/brain/bin/brain pull        # rafraîchit qonto/
~/brain/bin/brain clean       # hygiene (report seulement)
~/brain/bin/brain reindex
```
Types : `domain / decision / entity / concept / feedback`. Zéro appel modèle. Cité dans les réponses.

### B. Auto-memory Claude Code — `~/.claude/projects/-Users-julien/memory/`
Types : `user / feedback / project / reference`. Le modèle décide seul quoi persister (avec ton veto). Index dans `MEMORY.md` (toujours chargé, ≤200 lignes utiles).

**Règle de tri** :
- Fait durable, cross-conversation, technique → **brain**
- Préférence de collab, style, correction, "on m'a dit une fois" → **auto-memory**

**Piège** : dupliquer entre les deux systèmes → source de vérité floue. Un fait = un endroit.

---

## 15. Tracking : TASKS.md et STATUS.md

Depuis 2026-07-07, source de vérité tâches = **`~/Claude/TASKS.md`**. Toute tâche évoquée en session y est ajoutée, toute tâche finie y est cochée avec sa date.

STATUS.md par domaine :
- `~/Claude/Work/automation/STATUS.md`
- `~/Claude/Work/perso/Goupille/STATUS.md`
- `~/Claude/Life/transition/STATUS.md`

Fin de session : `/log` (ta command) → maj du STATUS.md du domaine touché.

---

## 16. MCP servers — outils externes plugés

MCP = Model Context Protocol. Un serveur MCP expose des tools au modèle (Notion, Linear, Slack, DB, filesystem étendu…).

### Voir les MCP connectés
```
/mcp
```

### Configurer (dans `settings.json`)
```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": { "NOTION_API_KEY": "secret_..." }
    }
  }
}
```

**Piège** : ajouter un MCP mal codé peut freezer le CLI au démarrage. Test-le en isolé avant de le mettre en config permanente.

---

## 17. Modes d'exécution

### Plan Mode
Lancement : `claude --permission-mode plan` ou command `/plan` (si tu l'as).
Le modèle **lit et propose un plan**, ne modifie rien. Tu approuves → sortie de plan mode → exécution.

Utile pour :
- Refactor multi-fichiers
- Design d'architecture
- Toute action à blast radius > 1 fichier

**Piège** : rester en plan mode alors que tu veux qu'il code → il boucle sur des propositions. Sors-en explicitement.

---

## 18. Boucles et scheduling

### `/loop` — répéter à intervalle
```
/loop 5m /brief                    # toutes les 5 min lance /brief
/loop 30s check les logs docker    # prompt libre toutes les 30 s
/loop /babysit-prs                 # sans intervalle → self-paced
```
S'arrête avec Ctrl+C ou `/exit`.

### `/schedule` — cron (agent distant)
```
/schedule create "chaque matin 8h, run /brief"
/schedule list
/schedule delete <id>
```
Crée un trigger Claude Code qui tourne côté serveur → pas besoin que ton laptop soit ouvert.

**Piège** : `/loop` sur un intervalle < 60s = spam de tokens. Le `dynamic` (sans interval) est souvent mieux.

---

## 19. Économiser le contexte (le budget cognitif du modèle)

Le prompt cache Anthropic a une TTL de 5 min. Chaque re-lecture du contexte au-delà = cache miss = plus lent + plus cher.

- **`/clear`** dès qu'une tâche est finie et que tu enchaînes sur une autre sans rapport
- **`/compact`** en session longue (session > 100 tours) pour libérer sans perdre le fil
- **Ne pas @-mention un gros fichier** juste "pour info" — laisse le modèle le lire via Read (partiel)
- **Sous-agents** pour toute exploration >3 queries → le résultat revient synthétisé, le raw ne pollue pas ton contexte
- **Éviter les logs verbeux** dans les Bash calls (utilise `| head`, `| tail`, filtres)

---

## 20. Économiser le budget (tokens $)

- Modèle : Haiku par défaut, Sonnet pour gros ; Opus **quand tu en as besoin**
- Prompt caching automatique : évite les modifications superficielles du prompt système
- **`/cost`** régulièrement pour calibrer
- Sessions longues → `/compact` au lieu de `/clear` (garde le cache actif si possible)
- Pas d'Opus pour formatter du markdown ou renommer une variable

**Ordre de grandeur** : Opus ≈ 5× Sonnet ≈ 12× Haiku sur les prix input/output.

---

## 21. Extensions et intégrations

- **VS Code / Cursor** : extension officielle "Claude Code" (diff live, apply patch, resume in terminal)
- **JetBrains** : plugin
- **Web** : `claude.ai/code` = même harness, session synchro
- **Desktop app** : Mac/Windows

**Piège** : lancer Claude Code dans 2 endroits en parallèle sur le même projet = les hooks se déclenchent 2×.

---

## 22. Statusline (bandeau en bas du CLI)

Affiche modèle / mode / dossier / tokens. Personnalisation via `settings.json` :
```json
{
  "statusLine": {
    "type": "command",
    "command": "echo \"[$(basename $PWD)] $(git branch --show-current 2>/dev/null)\""
  }
}
```
Skill dédié : sous-agent `statusline-setup`.

---

## 23. Workflow-type Julien (à copier-coller)

### Démarrage de session matinale
```
1. cd ~/Claude/Work/                   # ou le domaine du jour
2. claude                              # charge CLAUDE.md hiérarchique
3. /brief                              # ta command : brief matinal
4. lecture → priorisation → attaque de la 1re tâche
```

### Session harness LR DE
```
1. cd ~/Claude/Work/automation/Legal\ Requests/lr-de-harness/
2. claude
3. /log (fin) ou /todo (début) pour cadrer
4. Toujours challenger : problème réel ? bonne couche ?
5. Fin → maj STATUS.md du domaine + brain remember si fait durable
```

### Session coaching Python
```
1. cd ~/Claude/Work/perso/python/julien-python-journey/
2. claude
3. → CLAUDE.md projet chargé (méthode pédagogique)
4. Fin → /save si concept majeur + exercice entre-deux
```

### Session career / life
```
1. cd ~/Claude/Life/transition/
2. claude
3. Direct (mode career coach / life advisor auto-détecté)
```

---

## 24. Les pièges qui vont te mordre (top 12)

1. **Ouvrir CLI depuis `~/`** → tu perds le CLAUDE.md projet. Toujours ouvrir depuis le domaine visé.
2. **Empiler du volatile dans CLAUDE.md** → ta config gonfle. Volatile → STATUS.md.
3. **Demander un comportement récurrent en mémoire** ("souviens-toi de faire X à chaque X") → ça ne peut PAS marcher. Hook obligatoire (§10).
4. **Rester en Opus par défaut** → coût x5 pour rien. `/model haiku` pour du simple.
5. **`@` un fichier de 2000 lignes** → cache pété. Laisse le modèle lire avec Read.
6. **`bypassPermissions` en prod** → un `rm -rf` mal placé et tu pleures. Sandbox uniquement.
7. **Ne pas utiliser les sous-agents** pour l'exploration → contexte principal pollué de 500 résultats de grep.
8. **Ignorer `/compact`** en session > 100 tours → cache miss permanent, réponses molles.
9. **Inventer un nom de skill/agent** → tool call plante. Toujours vérifier la liste dispo.
10. **Écrire un slash command custom qui appelle un shell dangereux** → à traiter comme un hook.
11. **Deux instances Claude Code sur le même projet** → hooks x2, artefacts mélangés.
12. **Rédiger un prompt d'agent en 2 mots** → l'agent bricole. Brief comme un collègue qui vient d'entrer.

---

## 25. Debug rapide

| Symptôme | Piste |
|---|---|
| Une skill devrait triggerer, ne trigger pas | `/help` → est-elle listée ? Sinon vérifier `~/.claude/skills/<nom>/SKILL.md` frontmatter |
| Un hook ne s'exécute pas | `/hooks` puis tester la commande à la main |
| Un MCP est down | `/mcp` → status ; relancer le CLI |
| Le modèle "oublie" un fait | check `MEMORY.md` puis `brain recall` — souvent pas indexé |
| Session très lente | `/status` (taille contexte) → `/compact` |
| Tool refusé | `/permissions` → ajoute à l'allowlist ou `/update-config` |
| Sortie tronquée | modèle a hit `max_tokens`. Redemande "continue" ou switch modèle plus généreux |

---

## 26. Sécurité — les 5 règles non-négociables

1. **Jamais** `bypassPermissions` sur un projet contenant du prod.
2. **Jamais** de secret en clair dans `settings.json` versionné → utiliser `settings.local.json` (gitignored) ou variables d'env.
3. **Jamais** hook qui exécute une commande construite depuis input utilisateur non échappé.
4. **Toujours** review d'un skill / command / MCP tiers avant install (c'est du code qui tournera avec tes droits).
5. **Toujours** `/security-review` avant un push sur un projet sensible (LR DE, harness prod).

---

## 27. Ce qui doit devenir automatique

- **Ouvrir CLI depuis le bon dossier** (pas `~/`)
- **`/model haiku`** par défaut, upgrade explicite quand ça dépasse
- **`/compact` avant que la session grossisse**
- **Sous-agent Explore** dès qu'une recherche prend >3 queries
- **`brain recall`** avant toute réponse dépendant de la mémoire
- **STATUS.md à jour** en fin de session de travail
- **TASKS.md à jour** en cours de session
- **`/update-config`** pour toute règle "à chaque fois" — jamais dans un CLAUDE.md
- **`/security-review`** avant push sur prod
- **`/cost`** en fin de session longue pour calibrer

---

## Récap ultra-condensé (à relire avant de lancer)

```
Ouvrir depuis le bon dossier    cd <projet> && claude
Reprendre                        claude --resume  /  claude -c
Interrompre génération           Escape
Interrompre tool call            Ctrl + C
Nouvelle ligne                   Shift + Enter
Historique                       ↑ / Ctrl + R

Injecter un fichier              @path/to/file
Exécuter du shell inline         !ls -la
Custom command                   /brief, /todo, /log, /save, /log
Skill                            /last30days, /simplify, /update-config

Changer modèle                   /model haiku|sonnet|opus
Fast mode Opus                   /fast
Voir coût                        /cost
Voir contexte                    /status
Compresser contexte              /compact
Repartir de zéro                 /clear

Sous-agent recherche             Task → Explore
Sous-agent design                Task → Plan
Sous-agent recherche cross-src   /last30days

Hook automatique                 settings.json → hooks.<event>
Allowlist                        settings.json → permissions.allow
Skill config                     /update-config

Mémoire durable technique        ~/brain/bin/brain remember
Mémoire durable collab           auto-memory (MEMORY.md)
Tâches                           ~/Claude/TASKS.md
État volatile                    <domaine>/STATUS.md
```

---

## Où tu vas revoir tout ça

- **Chaque nouvelle session** : ctrl+F sur cette fiche AVANT d'improviser une commande.
- **Setup d'un nouveau projet** : sections 12-13-14 (settings + CLAUDE.md + STATUS.md).
- **Gain de vitesse** : sections 19-20 (contexte + budget).
- **Automatisation** : section 10 (hooks) + 8 (skills) + 18 (loop/schedule).
- **En parallèle** : `terminal-cheatsheet-2026-07-12.md` pour tout ce qui touche zsh AZERTY sous le CLI.
