# BotAmongUs
#  Discord Transparency & Privacy Demonstration Bot
## Démo académique — PoPETs 2026
Basé sur : "Bot Among Us", PoPETs 2026(1), pp. 296–320.

---

BotAmongUs est un bot Discord pédagogique conçu pour démontrer, de manière concrète, les enjeux de **transparence**, **collecte de données**, **permissions**, et **comportements ambigus** des bots dans les communautés en ligne.

Ce projet s’inscrit dans le cadre du cours *Sécurité des Données Personnelles* et  s’appuie sur les recommandations du papier 0016 - PoPETs 2026.

--- 

## 🎯 Objectifs du projet

- Illustrer comment un bot peut **collecter, analyser et exploiter** des données sans que les utilisateurs en soient pleinement conscients.
- Montrer l’importance de la **transparence**, des **permissions explicites** et du **consentement éclairé**.
- Comparer deux comportements :
  - **Mode Silent** : collecte minimale, comportement neutre.
  - **Mode Perspective** : analyse des messages, scoring, extraction d’informations.

---

## 🧩 Fonctionnalités principales

### 🔐 Gestion des permissions
- Commande `!permissions` affichant :
  - les permissions Discord accordées au bot
  - les intents activés
  - les capacités de collecte
  - les limites et garanties de confidentialité

### 🔄 Modes de fonctionnement
- **Module 1** `!mode silent` → bot minimaliste, aucune analyse
- **Module 2** `!mode perspective` → analyse des messages, scoring, extraction de signaux
- Stockage du mode actif dans `current_mode.txt`

### 📊 Dashboard & API
- Dashboard web (HTML/CSS/JS) affichant :
  - activité du bot
  - scores
  - logs anonymisés
  - mode actif
- API Flask exposant :
  - `/mode`
  - `/logs`
  - `/score`
  - `/permissions`

### 🗄️ Base de données
- SQLite (ou autre) pour stocker :
  - logs anonymisés
  - scores
  - événements
  - changements de mode

---

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/Rocklaye/BotAmongUs.git
cd BotAmongUs
```

### 2. Installer les dépendances
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ajouter le token de bot discord 

`TOKEN   = ""  # Collez votre token Discord ici`

### 4. Lancer le bot
```bash
python bot.py
```

### 5. Lancer l’API
```bash
python api.py
```
### 6 Ouvrir le dashboard Dashboard 
```bash
double-clic ou :
firefox dashboard.html
```

## 🧪 Commandes disponibles
Commande	Description
!permissions	Affiche les permissions, intents et capacités du bot
!mode	Affiche le mode actuel
!mode silent	Active le mode transparent/minimal
!mode perspective	Active le mode analyse/comportement ambigu
!help	Liste les commandes

## 🛡️ Sécurité & Confidentialité

- Les données sont anonymisées dans la base
- Le bot affiche clairement ce qu’il collecte
- Le dashboard expose les actions du bot en temps réel

## 📚 Contexte académique
Ce projet illustre :

- les risques liés aux bots Discord
- la facilité de collecter des données personnelles via un bot dans les serveurs discord
- l’importance de la transparence
- les bonnes pratiques de développement éthique


📄 Licence
Projet académique - non destiné à un usage commercial.