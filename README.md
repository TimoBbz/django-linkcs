# LinkCS Django App

## Description

Le but de cette application est de fournir l'auth ViaRézo à votre site et de simplifier les requêtes à LinkCS. Pour ce faire sont fournis :
- Un moteur d'authentification à l'auth ViaRézo
- Un middleware pour réauthentifier les utilisateurs via le _refresh token_
- Un modèle abstrait ajoutant l'id linkcs aux utilisateurs
- Une vue héritable permettant de faire des requêtes à LinkCS.

## Utilisation

### Exigences préliminaires

Pour utiliser ce projet, vous devez disposer :
- d'un client LinkCS permettant les méthodes d'authentification _authorization_code_ et _refresh_token_
- d'un projet Django avec l'application `django.contrib.auth` installée.

### Ajout à votre application

Cette application utilise l'application `django.contrib.auth`, elle doit donc être installée dans les paramètres du projet.

Pour ajouter cette application à votre projet, suivez les étapes :
1. Mettez le dossier _./linkcs_ à la racine de votre projet Django (vous pouvez cloner ce projet, puis créer un lien symbolique de l’application à votre projet)
2. Ajoutez l'application `linkcs` dans la variable `INSTALLED_APPS` du fichier _settings.py_, entre l'application `django.contrib.auth` et les applications qui en dépendent :
```
INSTALLED_APPS = [
    ...
    'django.contrib.auth',
    ...
    'linkcs',
    ...
]
```
3. Ajoutez le middleware `linkcs.middleware.OauthMiddleware` dans la variable `MIDDLEWARE` du fichier _settings.py_, après le middleware `django.contrib.auth.middleware.AuthenticationMiddleware` :
```
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'linkcs.middleware.OauthMiddleware',
    ...
]
```
4. Ajoutez le backend `linkcs.backends.OauthBackend` dans la variable AUTHENTICATION_BACKENDS du fichier _settings.py_. Le backend `django.contrib.auth.backends.ModelBackend` n'est nécessaire que si la connexion par identifiant et mot de passe est nécessaire.
```
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # optionnel
    'linkcs.backends.OauthBackend',
]
```

5. Définissez dans le fichier _settings.py_ les variables suivantes avec leurs valeurs :
- `CLIENT_ID` : l'id de votre client LinkCS
- `CLIENT_SECRET` : le secret de votre client LinkCS. **NE GITTEZ PAS CETTE VARIABLE**
- `LINKCS_SCOPE` : les scopes de votre client, séparés par des espaces dans une chaîne de caractères.
- `REDIRECT_URL` : l'url de redirection du protocole Oauth2, précisé dans votre client LinkCS.

6. Créez un modèle utilisateur, héritant du modèle abstrait `linkcs.models.AbstractLinkcsUser`, et donnez-le à la variable `AUTH_USER_MODEL` du fichier settings.py

7. Ajoutez les urls au fichier _./urls.py_ de votre projet :
```
urlpatterns = [
    ...
    path('linkcs/', include('linkcs.urls')),
    ...
]
```

### Utilisation

Cette application s'interface avec le système d'authentification de Django. Pour connecter un utilisateur via LinkCS, il doit être créé en base de données avec son id LinkCS (ne pas confondre avec le login) renseigné. Ensuite, l'utilisateur est connecté via une requête GET à la route _/linkcs/login_.

Pour faire une requête LinkCS, il faut créer une vue qui hérite de la vue linkcs.GraphQLView, et renseigner la variable `query` ou écraser la fonction `get_query(self, request)` (cela permet d'utiliser par exemple des paramètres passés dans la requête). L'access token de l'utilisateur est utilisé pour cette requête.

## Développement

### Contribuer

Pour contribuer au développement de cette application, vous pouvez cloner ce dépôt, créer un projet Django, et inclure l'application linkcs au projet avec un lien symbolique. Vous configurez ensuite le client comme décrit précédemment.

### Fonctionnalités à ajouter

- Choix des méthodes d'authentification
- Rendre l'installation de l'application plus "classique", comme un module par exemple
- Gérer les vues classiques de l'authentification lorsque le client est connecté avec LinkCS pour traiter proprement les cas qui ne fonctionnent pas avec l'authentification LinkCS (par exemple, prévenir proprement l'appel de la vue de réinitialisation de mot de passe).
- Configurer l'interface d'administration pour l'application
- Rendre la contribution plus "classique"
- Écrire des tests
