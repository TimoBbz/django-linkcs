from datetime import datetime
from http import HTTPStatus
import logging

from django.core.exceptions import ImproperlyConfigured
from requests import get, post, ConnectionError, RequestException, TooManyRedirects, Timeout, HTTPError

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.sessions.exceptions import InvalidSessionKey
from django.http import HttpResponse

AUTH_HOST = 'https://auth.viarezo.fr'
AUTH_AUTHORIZE_URL = f'{AUTH_HOST}/oauth/authorize/'
AUTH_TOKEN_URL = f'{AUTH_HOST}/oauth/token'
AUTH_USER_URL = f'{AUTH_HOST}/api/user/show/me'
LINKCS_API_URL = 'https://api.linkcs.fr/v1/graphql/'
logger = logging.getLogger(__name__)


class ServerError(RequestException):
    pass


class HttpResponseBadGateway(HttpResponse):
    status_code = HTTPStatus.BAD_GATEWAY


class HttpResponseGatewayTimeout(HttpResponse):
    status_code = HTTPStatus.GATEWAY_TIMEOUT


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE


def server_request_wrapper(method, *args, **kwargs):
    server_request = method(*args, **kwargs)
    if str(server_request.status_code).startswith('5'):
        raise ServerError
    server_request.raise_for_status()
    return server_request


def authenticate_server(request, **credentials):
    if 'code' not in credentials or 'state' not in credentials:
        return False

    if 'state' not in request.session.keys():
        return False

    if request.session['state'] != credentials['state']:
        return False

    auth_request = server_request_wrapper(post, AUTH_TOKEN_URL, headers={
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
    else:
        now_timestamp = datetime.timestamp(datetime.now())
        if request.session['expires_at'] < now_timestamp:
            raise ImproperlyConfigured('Access token refreshing should be '
                                       + 'handled by a middleware')

    auth_request = server_request_wrapper(get, AUTH_USER_URL, headers={
        'Authorization': f"Bearer {request.session['access_token']}"
    })

    return auth_request.json()


def get_profile_model():
    """
    Return the Profile model that is active in this project.
    """
    if not hasattr(settings, 'AUTH_PROFILE_MODEL'):
        raise ImproperlyConfigured("The variable AUTH_PROFILE_MODEL must be set in the settings")
    try:
        return django_apps.get_model(settings.AUTH_PROFILE_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("AUTH_PROFILE_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_PROFILE_MODEL refers to model '%s' that has not been installed" % settings.AUTH_PROFILE_MODEL
        )


class HandleGatewayErrorMixin:

    @staticmethod
    def handle_bad_gateway(request, *args, **kwargs):
        return HttpResponseBadGateway()

    @staticmethod
    def handle_gateway_timeout(request, *args, **kwargs):
        return HttpResponseGatewayTimeout()

    @staticmethod
    def handle_bad_request(request, *args, **kwargs):
        return HttpResponseServiceUnavailable()

    @classmethod
    def handle_gateway_error(cls, error: RequestException, request, *args, **kwargs):
        if error in (ConnectionError, ServerError, TooManyRedirects):
            return cls.handle_bad_gateway(request, *args, **kwargs)

        if error == Timeout:
            return cls.handle_gateway_timeout(request, *args, **kwargs)

        if error == HTTPError:
            return cls.handle_bad_request(request, *args, **kwargs)
