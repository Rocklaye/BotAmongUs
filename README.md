# BotAmongUs
## Démo académique — PoPETs 2026

Basé sur : Chou et al., "Bot Among Us", PoPETs 2026(1), pp. 296–320.

---

## Architecture

```
bot.py          → Bot Discord (collecte + notifications)
app.py          → API Flask (expose les données + gère le mode)
dashboard.html  → Interface standalone (ouvrir dans le navigateur)
privacy_data.db → Base SQLite (créée automatiquement)
current_mode.txt→ Fichier partagé bot ↔ flask (mode actuel)
```

## Deux modules

**Module 1 — Mode Silencieux** (défaut)
Reproduit ce que le papier dénonce (§4) : collecte silencieuse de tous
les messages et métadonnées, aucune notification aux membres.

**Module 2 — Mode Perspective**
Implémente les recommandations des auteurs (§5.3) :
- Notification quand le bot rejoint pour la 1ère fois (§5.3.1)
- Notification aux nouveaux membres dans #general (§5.3.5)
- Commande `!permissions` avec privacy nutrition label (§5.3.2)
- Switch de mode sans redémarrage via `!mode` ou le dashboard

## Installation

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Configuration Discord

1. https://discord.com/developers/applications → New Application
2. Bot → activer : Server Members Intent + Message Content Intent + Presence Intent
3. Reset Token → coller dans bot.py : TOKEN = "..."
4. OAuth2 → URL Generator → bot → Read Messages + Read History + Send Messages → inviter

## Lancement

```bash
# Terminal 1 — Bot
python bot.py

# Terminal 2 — API
python app.py

# Dashboard — double-clic ou :
firefox dashboard.html
```

## Commandes Discord

| Commande | Description |
|---|---|
| `!mode` | Switcher entre Module 1 et Module 2 |
| `!permissions` | Afficher intents, permissions et politique de données |
| `!stats` | Statistiques de collecte en temps réel |
| `!rapport` | Lien vers le dashboard |
| `!help` | Liste toutes les commandes |

## Lien papier

| Feature | Référence |
|---|---|
| Collecte silencieuse (Module 1) | §4.3, Tableau 2 |
| Notification premier join (Module 2) | §5.3.1 |
| Notification nouveau membre (Module 2) | §5.3.5 |
| `!permissions` — privacy nutrition label | §5.3.2, Kelley et al. 2009 |
| Switch de mode sans redémarrage | Notre contribution |
| Privacy Report Dashboard | §5.3.3 |
