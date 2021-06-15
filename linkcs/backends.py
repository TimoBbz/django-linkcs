from requests import get, post

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect

from . import AUTH_TOKEN_URL, AUTH_USER_URL

UserModel = get_user_model()


class OauthBackendMixin():

    def authenticate_linkcs(self, request, **credentials):
        if 'code' not in credentials or 'state' not in credentials:
            return None

        if not 'state' in request.session.keys():
            return None

        if request.session['state'] != credentials['state']:
            return None

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

    def get_linkcs_user(self, request):
        return get(AUTH_USER_URL, headers = {
            'Authorization': f"Bearer {request.session['access_token']}"
        })


class SessionOnlyOauthBackend(OauthBackendMixin, BaseBackend):

    def authenticate(self, request, **credentials):
        self.authenticate_linkcs(request, **credentials)
        return AnonymousUser()

    def get_user(self, user_id):
        return AnonymousUser()


class UserOauthBackend(OauthBackendMixin, ModelBackend):

    def authenticate(self, request, **credentials):
        self.authenticate_linkcs(request, **credentials)

        user_request = self.get_linkcs_user(request)

        try:
            return UserModel.objects.get(linkcs_id=user_request.json()['id'])
        except UserModel.DoesNotExist:
            return None


class CreateUserOauthBackend(OauthBackendMixin, ModelBackend):

    def get_defaults(self, request, user_request):
        return {
            'username': user_request['login'],
            'first_name': user_request['firstName'],
            'last_name': user_request['lastName'],
            'email': user_request['email'],
        }

    def authenticate(self, request, **credentials):
        self.authenticate_linkcs(request, **credentials)

        user_request = self.get_linkcs_user(request)

        return UserModel.objects.get_or_create(
            linkcs_id=user_request.json()['id'],
            defaults=self.get_defaults(request, user_request)
        )
