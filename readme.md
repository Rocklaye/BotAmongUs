## Nouvelle fonctionnalité : Transparence des permissions du bot

Afin de répondre aux enjeux de transparence et de protection de la vie privée identifiés dans l’article *“Bot Among Us: Exploring User Awareness and Privacy Concerns About Chatbots in Group Chats” (PoPETs 2026)*, une nouvelle fonctionnalité a été ajoutée au projet.

Cette fonctionnalité permet de rendre visibles les **intents et les permissions réelles du bot Discord**, afin que les utilisateurs puissent comprendre quelles données le bot peut potentiellement collecter ou utiliser.

---

### Commande Discord

Une nouvelle commande a été implémentée :
!permissions


Cette commande affiche directement dans Discord les capacités du bot.

Exemple de sortie :
Permissions du bot BotAmongUs

Intents activés :

Lire le contenu des messages : OUI
Voir les membres : OUI
Voir les présences : OUI

Permissions serveur :

Voir les salons : OUI
Lire l’historique : OUI
Envoyer des messages : OUI
Gérer les messages : NON
Bannir des membres : NON


Cette commande permet aux utilisateurs du serveur de vérifier facilement les accès du bot.

---

### Intégration dans le dashboard

Une nouvelle page **« Permissions du bot »** a été ajoutée dans le tableau de bord.

Cette page récupère les informations depuis l’API :
/api/permissions


Elle affiche :

- les **intents Discord activés**
- les **permissions du bot dans le serveur**

Cette interface permet d’améliorer la **transparence du système** et de rendre les capacités du bot plus compréhensibles pour les utilisateurs.

---

### Motivation de recherche

Cette fonctionnalité implémente deux recommandations importantes de l’article *Bot Among Us* :

- améliorer la **transparence des capacités des chatbots**
- permettre aux utilisateurs de **comprendre quelles données un bot peut accéder**

En rendant visibles les permissions du bot, cette extension contribue à réduire les **écarts entre les attentes des utilisateurs et les capacités réelles du chatbot**, ce qui constitue un enjeu important en matière de protection de la vie privée dans les conversations de groupe.
