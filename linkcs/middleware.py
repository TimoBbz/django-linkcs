from datetime import datetime
from requests import post, ConnectionError, HTTPError, Timeout

from django.conf import settings
from django.contrib.auth import logout

from . import AUTH_TOKEN_URL, ServerError, logger, server_request_wrapper


class OauthRefreshMiddleware:

    def handle_bad_gateway(self, request):
        logout(request)
        return self.get_response(request)

    def handle_gateway_timeout(self, request):
        logout(request)
        return self.get_response(request)

    def handle_bad_request(self, request):
        logger.error('Oauth request raised an HTTP error code, this is not '
                     'supposed to happen.')
        logout(request)
        return self.get_response(request)

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        now_timestamp = datetime.timestamp(datetime.now())
        if ('refresh_token' in request.session.keys() and
                request.session['expires_at'] < now_timestamp):
            try:
                auth_request = server_request_wrapper(
                    post,
                    AUTH_TOKEN_URL,
                    headers={
                        'Content-type': 'application/x-www-form-urlencoded'
                    }, data={
                        'grant_type': 'refresh_token',
                        'refresh_token': request.session['refresh_token'],
                        'redirect_uri': settings.AUTH_REDIRECT_URL,
                        'client_id': settings.CLIENT_ID,
                        'client_secret': settings.CLIENT_SECRET,
                    })
            except (ConnectionError, ServerError):
                return self.handle_bad_gateway(request)
            except HTTPError:
                return self.handle_bad_request(request)
            except Timeout:
                return self.handle_gateway_timeout(request)

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
