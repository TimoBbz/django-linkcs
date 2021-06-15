# LinkCS Django App

## Description

Le but de cette application est de fournir l'auth ViaRézo à votre site et de simplifier les requêtes à LinkCS. Pour ce faire sont fournis :
- Trois moteurs d'authentification à l'auth ViaRézo
- Deux intergiciel pour réauthentifier les utilisateurs via le _refresh token_ ou détruire leur session
- Un modèle abstrait ajoutant l'id linkcs aux utilisateurs, ainsi qu'une permission _'request_linkcs'_.
- Des vues héritables permettant de faire des requêtes à LinkCS.

## Utilisation

### Exigences préliminaires

Pour utiliser ce projet, vous devez disposer :
- d'un client LinkCS permettant les méthodes d'authentification _authorization_code_ et _refresh_token_
- d'un projet Django avec l'application `django.contrib.auth` installée.

### Ajout à votre application

Cette application utilise l'application `django.contrib.auth`, elle doit donc être installée dans les paramètres du projet.

Pour ajouter cette application à votre projet, suivez les étapes :
1. Construire l'application linkcs : cloner ce dépôt, lancer la commande `python3 setup.py sdist` et copier l'archive générée hors du dépôt. Le dépôt peut être supprimé.
2. Installer l'application linkcs : `pip3 install --user chemin/vers/archive`
3. Ajoutez l'application `linkcs` dans la variable `INSTALLED_APPS` du fichier _settings.py_, entre l'application `django.contrib.auth` et les applications qui en dépendent :
```python
INSTALLED_APPS = [
    ...
    'django.contrib.auth',
    ...
    'linkcs',
    ...
]
```
4. Si vous souhaitez réauthentifier par refresh token les utilisateurs dont l'access token a expiré, ajoutez l'intergiciel `linkcs.middleware.OauthRefreshMiddleware` dans la variable `MIDDLEWARE` du fichier _settings.py_, après l'intergiciel `django.contrib.auth.middleware.AuthenticationMiddleware` :
```python
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'linkcs.middleware.OauthRefreshMiddleware',
    ...
]
```
Dans le cas contraire, pour détruire les sessions dont l'access token a expiré, utilisez l’intergiciel `linkcs.middleware.OauthNoRefreshMiddleware` à la place.
5. 3 moteurs d’authentification sont disponible. `linkcs.backends.UserOauthBackend` authentifie les utilisateurs existant en base de données, `linkcs.backends.CreateUserOauthBackend` crée dans la base de donnée les utilisateurs manquants et `linkcs.backends.SessionOnlyOauthBackend` n'utilise pas le modèle User de l'authentification. Ajoutez le moteur d'authentification choisi dans la variable AUTHENTICATION_BACKENDS du fichier _settings.py_. Le moteur d'authentification `django.contrib.auth.backends.ModelBackend` n'est nécessaire que si la connexion par identifiant et mot de passe est nécessaire.
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # optionnel
    'linkcs.backends.BackendChoisi',
]
```

6. Définissez dans le fichier _settings.py_ les variables suivantes avec leurs valeurs :
- `CLIENT_ID` : l'id de votre client LinkCS
- `CLIENT_SECRET` : le secret de votre client LinkCS. **NE GITTEZ PAS CETTE VARIABLE**
- `LINKCS_SCOPE` : les scopes de votre client, séparés par des espaces dans une chaîne de caractères.
- `AUTH_REDIRECT_URL` désigne l'url de redirection fourni au serveur OAuth2
- `LOGIN_URL` désigne l'url de redirection des utilisateurs non connectés. Pointe par défaut sur _/accounts/login/
- `LOGIN_REDIRECT_URL` désigne l'url de redirection des utilisateurs connectés. Pointe par défaut sur _/accounts/profile/_
- `LINKCS_LOGIN_REDIRECT_URL` peut être renseignée pour fournir une redirection différente aux utilisateurs qui se connectent via LinkCS. Si elle n'est pas renseignée, la valeur de `LOGIN_REDIRECT_URL` sera utilisée.

7. Créez un modèle utilisateur, héritant du modèle abstrait `linkcs.models.AbstractLinkcsUser`, et donnez-le à la variable `AUTH_USER_MODEL` du fichier settings.py

8. Deux jeux d'urls fondés sur `django.contrib.auth.urls` sont proposés. `linkcs.urls.both` permet d’utiliser les deux authentifications en parallèle et `linkcs.urls.linkcs` fournit les urls pour utiliser l’authentification LinkCS seulement. Ajoutez les urls au fichier _./urls.py_ de votre projet :
```python
urlpatterns = [
    ...
    path('accounts/', include('linkcs.urls.urlschoisis')),
    ...
]
```

### Personalisation

#### Moteurs d'authentification

Le moteur d'authentification `linkcs.backends.CreateUserOauthBackend` crée des utilisateurs avec les paramètres par défaut suivants :
- `'username'` : Le login LinkCS,
- `'first_name'` : Le prénom sur LinkCS,
- `'last_name'` : Le nom de famille sur LinkCS,
- `'email'` : L'email principal sur LinkCS.

Pour personaliser ces paramètres par défaut, il faut créer un moteur héritant de la vue `linkcs.backend.CreateUserOauthBackend` et écraser la fonction `get_defaults(self, request, user_request)`, où `user_request` désigne le résultat de la requête à _https://auth.viarezo.fr/api/user/show/me_, sous forme de dictionnaire.

Le moteur d'authentification `linkcs.backends.SessionOnlyOauthBackend` authentifie les utilisateurs et enregistre les informations de `user_request` dans la session.

#### Urls fournis

L’application fournit deux jeux d'urls. Les vues correspondantes sont fondées sur des classes donc peuvent être personalisées par héritage. Les vues utilisent des templates qui doivent être créés par l'utilisateur dans le dossier _templates/registration_.

##### `linkcs.urls.both`

Ce jeu fournit les modèles d'urls suivants :
```python
accounts/auth/ [name='oauth_redirect_uri']
accounts/login/ [name='login']
accounts/login/linkcs [name='login_linkcs']
accounts/login/credentials [name='login_credentials']
accounts/logout/ [name='logout']
accounts/password_change/ [name='password_change']
accounts/password_change/done/ [name='password_change_done']
accounts/password_reset/ [name='password_reset']
accounts/password_reset/done/ [name='password_reset_done']
accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
accounts/reset/done/ [name='password_reset_complete']
```
La plupart des vues utilisées sont les vues de `django.contrib.auth.views`, mise à part les vues suivantes :
- LinkCSRedirect (utilisée dans l'URL nommée `oauth_redirect_uri`) est l'url vers laquelle le serveur OAuth2 redirige. Elle authentifie l'utilisateur tout en vérifiant la variable state, puis le cas échéant, le redirige de la même manière que la vue `django.contrib.auth.views.LoginView`.
- LoginChoice (utilisée dans l'URL nommée `login`), fondée sur `django.views.base.TemplateView`, remplit le gabarit _registration/login_choice.html_ et fournit les variables de contexte `login_linkcs_url` et `login_credentials_url` contenant les urls vers les vues utilisées dans les urls nommés respectivement `login_linkcs` et `login_credentials` auxquels on a ajouté le corps de la requête GET vers l’url nommé `login`.
- LinkCSLogin (utilisée dans l'URL nommée `login_linkcs`) redirige vers le serveur OAuth2 tout en passant la variable `next` en session pour une redirection future.
- L’url nommée `login_credentials` utilise la vue `django.contrib.auth.views.LoginView`.
- PasswordChangeView (utilisée dans l’URL nommée `password_change`) est fondée sur la vue `django.contrib.auth.views.PasswordChangeView`, mais vérifie avant que l’utilisateur n’est pas connecté via LinkCS à l'aide de la permission _'request_linkcs'_.

##### `linkcs.urls.linkcs`

Ce jeu fournit les modèles d'urls suivants :
```python
accounts/auth/ [name='oauth_redirect_uri']
accounts/login/ [name='login']
accounts/logout/ [name='logout']
```
Les vues utilisées sont respectivement les vues LinkCSRedirect, LinkCSLogin et `django.contrib.auth.views.LogoutView`.

#### Requêtes à LinkCS

Pour faire une requête LinkCS, il faut créer une vue qui hérite de la vue `linkcs.views.GraphQLView` ou du mixin `linkcs.views.GraphQLMixin`, et renseigner la variable `query` ou écraser la fonction `get_query(self, request)` (cela permet d'utiliser par exemple des paramètres passés dans la requête). Pour passer des variables à la requête GraphQL, les variables sont renseignées via la variable `variables` ou la fonction `get_variables(self, request)`.
Pour accéder au résultat de la requête, il faut utiliser la fonction `get_graphql(self, cached=True)`. Par défaut le résultat est caché, ce comportement peut être changé passant `cached=False` lors de l’appel de la fonction.
L'access token de l'utilisateur est utilisé pour cette requête. Dans le cas où la vue est utilisée plutôt que le mixin, la réponse est un objet `django.http.JsonResponse`.

## Développement

### Contribuer

Pour contribuer au développement de cette application, vous pouvez cloner ce dépôt, créer un projet Django, et inclure l'application linkcs au projet avec un lien symbolique. Vous configurez ensuite le client comme décrit précédemment.

### Fonctionnalités à ajouter

- Faire une pipeline qui publie les packages
- Choix des méthodes d'authentification
- Configurer l'interface d'administration pour l'application
- Rendre la contribution plus "classique"
- Écrire des tests
