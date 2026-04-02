# BotAmongUs 
## Démo - PoPETs 2026-0016

---

## Installation
### 1. Cloner le repo
`git clone https://github.com/tonpseudo/BotAmongUs.git`

`cd BotAmongUs`
### 2. Créer un environnement virtuel
```bash 
python -m venv venv
source venv/bin/activate   # Linux
venv\Scripts\activate      # Windows
```

### 3. Installer les dépendances
`pip install -r requirements.txt`

### 4. Ajouter votre token Discord dans bot.py
```bash 
TOKEN = "" 
```

### 5. Lancer le bot
`python bot.py`

### 6. Lancer le dashboard Flask
`python app.py`

### 7 Ouvrir le dashboard 
`firefox dashboard.html ou (double-clic)`

# Implémentation de BotAmongUs

## Module 1 - Mode silencieux (ce que les auteurs dénoncent)

le bot lit tout
le bot collecte tout
le bot ne parle pas
le bot n’est pas visible
le bot ne demande pas de consentement
le bot ne notifie personne
le bot stocke les messages même supprimés
le bot reconstruit l’identité et l’activité

## Objectif pédagogique :
Montrer que les risques décrits dans l’article sont réels, reproductibles et invisibles pour les utilisateurs.

## Module 2 - Mode perspective (ce que les auteurs recommandent)

Ici le but est d’apporter des solutions au problème que le papier dénonce et de les implémenter réellement.

### A) Notifier les utilisateurs qu’un chatbot est là

#### 1) Un message si c’est la première fois que le bot rejoint

Le bot doit envoyer un message dans un canal (ex : #general).

Exemple :
Bonjour ! Je suis Chatbot1
Je viens d’être ajouté à ce serveur.

Voici ce que je peux voir :
– Messages publics
– Métadonnées (pseudo, avatar, rôle)
– Activité dans les canaux

Pour plus d’informations : tapez !permissions.


---

#### 2) Un message si le bot était déjà là

Quand un NOUVEL utilisateur rejoint, le bot lui envoie un message :

- soit en DM  
- soit dans un canal dédié (ex : #bienvenue)

Exemple :
Rappel : un bot nommé ChatBot1 est présent dans ce serveur.
Il a pour rôle : modération / analyse / etc.

Tapez !permissions pour voir ce qu’il peut lire.


---

### Objectif pédagogique

Ajouter de la transparence et montrer que c’est possible.
