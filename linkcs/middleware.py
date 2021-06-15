from datetime import datetime
from requests import post

from django.conf import settings

from . import AUTH_TOKEN_URL


class OauthRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        if 'refresh_token' in request.session.keys() and request.session['expires_at'] < datetime.timestamp(datetime.now()):
            auth_request = post(AUTH_TOKEN_URL, headers={
                'Content-type': 'application/x-www-form-urlencoded'
            }, data={
                'grant_type': 'refresh_token',
                'refresh_token': request.session['refresh_token'],
                'redirect_uri': settings.AUTH_REDIRECT_URL,
                'client_id': settings.CLIENT_ID,
                'client_secret': settings.CLIENT_SECRET,
            })

            deserialized = auth_request.json()

            request.session['access_token'] = deserialized['access_token']
            request.session['expires_at'] = deserialized['expires_at']
            request.session['refresh_token'] = deserialized['refresh_token']

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response


class OauthNoRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        if request.session['expires_at'] < datetime.timestamp(datetime.now()):
            request.session.clear()

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
