"""""""""""""""""
LinkCS Django App
"""""""""""""""""

Le but de cette application est de fournir l'auth ViaRézo à votre site et de simplifier les requêtes à LinkCS. Pour ce faire sont fournis :
- Un moteur d'authentification à l'auth ViaRézo
- Un middleware pour réauthentifier les utilisateurs via le *refresh token*
- Un modèle abstrait ajoutant l'id linkcs aux utilisateurs
- Une vue héritable permettant de faire des requêtes à LinkCS.

===========
Utilisation
===========
