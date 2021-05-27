from requests import get, post

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.shortcuts import redirect

from . import AUTH_TOKEN_URL, AUTH_USER_URL

UserModel = get_user_model()


class OauthBackend(ModelBackend):

    def authenticate(self, request, **credentials):
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
            'redirect_uri': settings.REDIRECT_URL,
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
        })

        deserialized = auth_request.json()
        request.session['access_token'] = deserialized['access_token']
        request.session['expires_at'] = deserialized['expires_at']
        request.session['refresh_token'] = deserialized['refresh_token']

        user_request = get(AUTH_USER_URL, headers = {
            'Authorization': f"Bearer {request.session['access_token']}"
        })

        try:
            return UserModel.objects.get(linkcs_id=user_request.json()['id'])
        except UserModel.DoesNotExist:
            return None
