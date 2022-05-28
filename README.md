# LinkCS Django App

## Description

Le but de cette application est de fournir l'auth ViaRézo à votre site et de simplifier les requêtes à LinkCS. Pour ce
faire sont fournis :

- Trois moteurs d'authentification à l'auth ViaRézo
- Deux intergiciels, pour réauthentifier les utilisateurs via le _refresh token_ ou détruire leur session
- Un modèle abstrait ajoutant l'id linkcs aux utilisateurs, ainsi qu'une permission _'request_linkcs'_.
- Des vues héritables permettant de faire des requêtes à LinkCS.

## Utilisation

### Exigences préliminaires

Pour utiliser ce projet, vous devez disposer :

- d'un client LinkCS permettant les méthodes d'authentification _authorization_code_ et _refresh_token_
- d'un projet Django avec l'application `django.contrib.auth` installée.

### Ajout à votre application

Cette application utilise l'application `django.contrib.auth`, elle doit donc être installée dans les paramètres du
projet.

Pour ajouter cette application à votre projet, suivez les étapes :

1. Installez l'application depuis le dépôt de paquets du
   projet : `pip install django-linkcs --extra-index-url https://__token__:personnalBR6mUvWsAFgGqdon6Xo@gitlab.viarezo.fr/api/v4/projects/2612/packages/pypi/simple`

2. Ajoutez l'application `linkcs` dans la variable `INSTALLED_APPS` du fichier _settings.py_, entre
   l'application `django.contrib.auth` et les applications qui en dépendent :

```python
INSTALLED_APPS = [
    ...
    'django.contrib.auth',
    ...
    'linkcs',
    ...
]
```

3. Si vous souhaitez réauthentifier par refresh token les utilisateurs dont l'access token a expiré, ajoutez
   l'intergiciel `linkcs.middleware.OauthRefreshMiddleware` dans la variable `MIDDLEWARE` du fichier _settings.py_,
   après l'intergiciel `django.contrib.auth.middleware.AuthenticationMiddleware` :

```python
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'linkcs.middleware.OauthRefreshMiddleware',
    ...
]
```

Dans le cas contraire, pour détruire les sessions dont l’access token a expiré, utilisez
l’intergiciel `linkcs.middleware.OauthNoRefreshMiddleware` à la place.

4. 3 moteurs d’authentification sont disponible. `linkcs.backends.UserOauthBackend` authentifie les utilisateurs
   existant en base de données, `linkcs.backends.CreateUserOauthBackend` crée dans la base de donnée les utilisateurs
   manquants et `linkcs.backends.SessionOnlyOauthBackend` n'utilise pas le modèle User de l'authentification. Ajoutez le
   moteur d'authentification choisi dans la variable AUTHENTICATION_BACKENDS du fichier _settings.py_.

Le moteur d'authentification `django.contrib.auth.backends.ModelBackend` n'est nécessaire que si la connexion par
identifiant et mot de passe est nécessaire.

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # optionnel
    'linkcs.backends.BackendChoisi',
]
```

5. Définissez votre modèle utilisateur. L’application fournit un profil ajoutant le champ linkcs_id au modèle 
utilisateur. Il est automatiquement utilisé lorsque l’application LinkCS est utilisée.


6. Définissez dans le fichier _settings.py_ les variables suivantes avec leurs valeurs :

- `CLIENT_ID` : l'id de votre client LinkCS
- `CLIENT_SECRET` : le secret de votre client LinkCS. **NE GITTEZ PAS CETTE VARIABLE**
- `LINKCS_SCOPE` : les scopes de votre client, séparés par des espaces dans une chaîne de caractères.
- `AUTH_REDIRECT_URL` désigne l’url de redirection fournie au serveur OAuth2
- `LOGIN_URL` (facultative) désigne l’url de redirection des utilisateurs non connectés. Pointe par défaut sur
  _/accounts/login/_
- `LOGIN_REDIRECT_URL` (facultative) désigne l’url de redirection des utilisateurs connectés. Pointe par défaut sur
  _/accounts/profile/_
- `LINKCS_LOGIN_REDIRECT_URL` (facultative) peut être renseignée pour fournir une redirection différente aux
  utilisateurs qui se connectent via LinkCS. Si elle n'est pas renseignée, la valeur de `LOGIN_REDIRECT_URL` sera
  utilisée.

7. Deux jeux d’urls fondés sur `django.contrib.auth.urls` sont proposés. `linkcs.urls.both` permet d’utiliser les deux
   authentifications en parallèle et `linkcs.urls.linkcs` fournit les urls pour utiliser l’authentification LinkCS
   seulement. Ajoutez les urls au fichier _./urls.py_ de votre projet :

```python
urlpatterns = [
    ...
    path('accounts/', include('linkcs.urls.urlschoisis')),
    ...
]
```

### Personalisation

#### Moteurs d'authentification

Les moteurs d'authentification utilisent la bibliothèque `requests`, qui lève des erreurs en cas de soucis lors de la
connexion au serveur. Le moteur d'authentification n'est pas censé lever d'erreurs, donc par défaut les erreurs sont
journalisées. Pour que les erreurs soient levées, il suffit de créer un backend héritant (dans cet ordre)
de `linkcs.backends.CrashOnErrorMixin` et du backend choisi. Celles-ci seront alors gérées dans la vue `LinkCSRedirect`,
voir plus bas.

Le moteur d'authentification `linkcs.backends.CreateUserOauthBackend` crée des utilisateurs avec les paramètres par
défaut suivants :

- `'linkcs_id'` : L’ID LinkCS,
- `'username'` : Le login LinkCS,
- `'first_name'` : Le prénom sur LinkCS,
- `'last_name'` : Le nom de famille sur LinkCS,
- `'email'` : L'email principal sur LinkCS.

Pour personaliser ces paramètres par défaut, il faut créer un moteur héritant de la
vue `linkcs.backend.CreateUserOauthBackend` et surcharger la fonction `get_defaults(self, request, user_request)`,
où `user_request` désigne le résultat de la requête à _https://auth.viarezo.fr/api/user/show/me_, sous forme de
dictionnaire.

Le moteur d'authentification `linkcs.backends.SessionOnlyOauthBackend` authentifie les utilisateurs et enregistre les
informations de `user_request` dans la session, à la clé `linkcs`.

#### Urls fournis

L’application fournit deux jeux d'urls. Les vues correspondantes sont fondées sur des classes donc peuvent être
personalisées par héritage. Les vues utilisent des templates qui doivent être créés par l'utilisateur dans le dossier _
templates/registration_.

##### `linkcs.urls.both`

Ce jeu fournit les modèles d'urls suivants :

```python
accounts/auth/ [name='oauth_redirect_uri']
accounts/login/ [name='login']
accounts/login/linkcs [name='login_linkcs']
accounts/login/failed [name='login_failed']
accounts/logout/ [name='logout']
accounts/password_change/ [name='password_change']
accounts/password_change/done/ [name='password_change_done']
accounts/password_reset/ [name='password_reset']
accounts/password_reset/done/ [name='password_reset_done']
accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
accounts/reset/done/ [name='password_reset_complete']
```

La plupart des vues utilisées sont les vues de `django.contrib.auth.views`, mise à part les vues suivantes :

- LinkCSRedirect (utilisée dans l'URL nommée `oauth_redirect_uri`) est l'url vers laquelle le serveur OAuth2 redirige.
  Elle authentifie l'utilisateur tout en vérifiant la variable state, puis le cas échéant, le redirige de la même
  manière que la vue `django.contrib.auth.views.LoginView`.
- LoginChoice (utilisée dans l'URL nommée `login`), fondée sur `django.views.base.TemplateView`, remplit le gabarit _
  registration/login_choice.html_ et fournit les variables de contexte `login_linkcs_url` et `login_credentials_url`
  contenant les urls vers les vues utilisées dans les urls nommés respectivement `login_linkcs` et `login_credentials`
  auxquels on a ajouté le corps de la requête GET vers l’url nommé `login`.
- LinkCSLogin (utilisée dans l'URL nommée `login_linkcs`) redirige vers le serveur OAuth2 tout en passant la
  variable `next` en session pour une redirection future.
- L'URL nommée `login_failed` est utilisée en cas d'échec de l'authentification via LinkCSLogin. Ici, elle redirige
  simplement vers `login`. Elle est utile pour le modèle d'URL 
- L’url nommée `login_credentials` utilise la vue `django.contrib.auth.views.LoginView`.
- PasswordChangeView (utilisée dans l’URL nommée `password_change`) est fondée sur la
  vue `django.contrib.auth.views.PasswordChangeView`, mais vérifie avant que l’utilisateur n’est pas connecté via
  LinkCS.

__Attention : la déconnexion détruit la session, mais ne déconnecte pas de l'oauth.__

##### `linkcs.urls.linkcs`

Ce jeu fournit les modèles d'urls suivants :

```python
accounts/auth/ [name='oauth_redirect_uri']
accounts/login/ [name='login']
accounts/login/failed [name='login_failed']
accounts/logout/ [name='logout']
```

Les vues utilisées sont respectivement les vues LinkCSRedirect, LinkCSLogin et `django.contrib.auth.views.LogoutView`,
ainsi que la vue LoginFailedView, qui affiche une erreur 403 Unauthorized. Cette vue est nécessaire pour éviter les
rebonds infinis. En effet, l'URL nommé `login` renvoie vers l'oauth, qui redirige vers `oauth_redirect_uri`, qui en
cas d'échec redirige vers `login_failed`. Si `login_failed` redirigeait vers `login`, on aurait une boucle infinie en
cas d’échec, donc le module prend le parti d'afficher une erreur 403. Ce comportement peut être modifié, en 
surchargeant l'URL nommé `login_failed`.

#### Gestion des permissions sur les vues

Deux mixins de restriction d'accès sont fournis pour gérer l'accès aux vues:

- `linkcs.views.UserLinkCSMixin` permet de s’assurer que l'utilisateur peut se connecter à LinkCS.
- `linkcs.views.UserNotLinkCSMixin` autorise les cas contraires.

#### Requêtes à LinkCS

Pour faire une requête LinkCS, il faut créer une vue qui hérite de la vue `linkcs.views.GraphQLView` ou du
mixin `linkcs.views.GraphQLMixin`, et renseigner la variable `query` ou surcharger la
fonction `get_query(self, request)` (cela permet d'utiliser par exemple des paramètres passés dans la requête). Pour
passer des variables à la requête GraphQL, les variables sont renseignées via la variable `variables` ou la
fonction `get_variables(self, request)`. Pour accéder au résultat de la requête, il faut utiliser la
fonction `get_result(self)`. Par défaut le résultat est caché via le décorateur @cached_property, ce comportement peut
être changé modifiant la fonction `get_result(self)`. L'access token de l'utilisateur est utilisé pour cette requête.
Dans le cas où la vue est utilisée plutôt que le mixin, la réponse est un objet `django.http.JsonResponse`.

#### Gestion des erreurs

Lors de la connexion au serveur, certaines erreurs de connexion peuvent se produire. Par défaut le comportement suivant
est adopté :

- Dans la vue `LinkCSRedirect` et le mixin `GraphQLMixin`, une erreur 502 (BAD GATEWAY), 503 (SERVICE_UNAVAILABLE) ou
  504 (GATEWAY TIMEOUT) peut être renvoyée.
- Dans l'intergiciel `OauthRefreshMiddleware`, l'utilisateur est déconnecté en cas d'erreur. Ce comportement peut être
  personnalisé. Les objets implémentent ces comportements dans des méthodes intitulées
  respectivement `handle_bad_gateway`, `handle_bad_request` et `handle_gateway_timeout` (`handle_bad_request` gère les
  requêtes erronnées de la part du site client, qui renvoit donc par défaut une erreur 503 à son propre client). Ces
  méthodes renvoient un objet réponse. dans le cas des vues, les méthodes prennent en argument la réponse initiale
  donnée par dispatch. Enfin, pour implémenter la gestion des erreurs dans des vues customisées, le
  mixin `HandleGatewayErrorMixin` peut être utilisé. (Le placer après les Mixin de contrôle d'accès.)

On notera que le serveur n'est jamais censé renvoyer une erreur HTTP 400 lors de la récupération de tokens puisque les
requêtes concernées sont immuables.

## Développement

### Contribuer

Pour contribuer au développement de cette application, vous pouvez cloner ce dépôt, créer un projet Django, et inclure
l'application linkcs au projet avec un lien symbolique (cela permet de recharger automatiquement l'application à chaque
modification, sans la reconstruire). Vous configurez ensuite le client comme décrit précédemment.

### Stratégie git

Le dépôt est configuré pour publier un paquet à chaque tag de version (qui doit correspondre à l'étiquette de version).
Il est fortement conseillé d'utiliser la commande ```git tag v`python3 setup.py --version` ``` afin de se rendre compte
des erreurs de version lors de l'étiquetage plutôt qu'après avoir poussé l'étiquette

Jusqu'à la version 1, on itère les version v0.x, puis ensuite on suit le versionnage sémantique (version majeure,
version mineure et patch). Si un patch est nécessaire, créez la branche _v8.6.x_ (ou tout autre version majeure et
mineure), et travaillez dessus.

### Fonctionnalités à ajouter

- Choix des méthodes oauth de récupération du token (actuellement, les méthodes "authorization_code" et "refresh_token"
  sont nécessaires)
- Configurer l'interface d'administration pour l'application (ajout d’utilisateur de type LinkCS ou non, avec une
  fonction de recherche parmi les utilisateurs depuis LinkCS)
- Écrire des tests
