from requests import get, post

from django.conf import settings
from django.contrib.sessions.exceptions import InvalidSessionKey

AUTH_HOST = 'https://auth.viarezo.fr'
AUTH_AUTHORIZE_URL = f'{AUTH_HOST}/oauth/authorize/'
AUTH_TOKEN_URL = f'{AUTH_HOST}/oauth/token'
AUTH_USER_URL = f'{AUTH_HOST}/api/user/show/me'
LINKCS_API_URL = 'https://api.linkcs.fr/v1/graphql/'


def authenticate_server(request, **credentials):
    if 'code' not in credentials or 'state' not in credentials:
        return False

    if 'state' not in request.session.keys():
        return False

    if request.session['state'] != credentials['state']:
        return False

    auth_request = post(AUTH_TOKEN_URL, headers={
        'Content-type': 'application/x-www-form-urlencoded'
    }, data={
        'grant_type': 'authorization_code',
        'code': credentials['code'],
        'redirect_uri': settings.AUTH_REDIRECT_URL,
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
    })

    deserialized = auth_request.json()
    request.session['access_token'] = deserialized['access_token']
    request.session['expires_at'] = deserialized['expires_at']
    request.session['refresh_token'] = deserialized['refresh_token']
    return True


def get_linkcs_user(request):
    if 'access_token' not in request.session.keys():
        raise InvalidSessionKey
    auth_request = get(AUTH_USER_URL, headers={
        'Authorization': f"Bearer {request.session['access_token']}"
    })
    return auth_request.json()
