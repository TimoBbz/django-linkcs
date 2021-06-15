from requests import get, post

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.exceptions import InvalidSessionKey

from . import AUTH_TOKEN_URL, AUTH_USER_URL

UserModel = get_user_model()


def authenticate_server(request, **credentials):
    if not 'code' in credentials or not 'state' in credentials:
        return False

    if not 'state' in request.session.keys():
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
    if not 'access_token' in request.session.keys():
        raise InvalidSessionKey
    auth_request = get(AUTH_USER_URL, headers = {
        'Authorization': f"Bearer {request.session['access_token']}"
    })
    return auth_request.json()


class SessionOnlyOauthBackend(BaseBackend):

    def fill_session(self, request):
        user_request = get_linkcs_user(request)
        request.session.update(user_request)

    def authenticate(self, request, **credentials):
        if authenticate_server(request, **credentials):
            self.fill_session(request)
            return AnonymousUser()
        return None

    def get_user(self, user_id):
        return AnonymousUser()


class UserOauthBackend(ModelBackend):

    def authenticate(self, request, **credentials):
        if not authenticate_server(request, **credentials):
            return None

        user_request = get_linkcs_user(request)

        try:
            return UserModel.objects.get(linkcs_id=user_request['id'])
        except UserModel.DoesNotExist:
            return None


class CreateUserOauthBackend(ModelBackend):

    def get_defaults(self, request, user_request):
        return {
            'username': user_request['login'],
            'first_name': user_request['firstName'],
            'last_name': user_request['lastName'],
            'email': user_request['email'],
        }

    def authenticate(self, request, **credentials):
        if not authenticate_server(request, **credentials):
            return None

        user_request = get_linkcs_user(request)

        return UserModel.objects.get_or_create(
            linkcs_id=user_request['id'],
            defaults=self.get_defaults(request, user_request)
        )
