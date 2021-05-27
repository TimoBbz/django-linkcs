from requests import get, post

from django.conf import settings


AUTH_HOST = 'https://auth.viarezo.fr'
AUTH_TOKEN_URL = f'{AUTH_HOST}/oauth/token'
AUTH_USER_URL = f'{AUTH_HOST}/api/user/show/me'
LINKCS_API_URL = 'https://api.linkcs.fr/v1/graphql/'
