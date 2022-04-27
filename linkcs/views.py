from datetime import datetime
from random import choice
from string import ascii_letters
from urllib.parse import urlencode
from requests import get, RequestException

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.sessions.exceptions import InvalidSessionKey
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.views.generic.base import RedirectView, View, TemplateView
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.functional import cached_property

from . import (
    AUTH_AUTHORIZE_URL, LINKCS_API_URL, HttpResponseServiceUnavailable, logger, server_request_wrapper,
    get_profile_model, HandleGatewayErrorMixin)

UserModel = get_user_model()
if has_profile := hasattr(settings, "AUTH_PROFILE_USER"):
    ProfileModel = get_profile_model()


class LinkCSLogin(RedirectView, LoginView):
    # Uses LoginView to put the redirect url into session
    state = ''.join(choice(ascii_letters) for _ in range(10))
    body = {
        'redirect_uri': settings.AUTH_REDIRECT_URL,
        'client_id': settings.CLIENT_ID,
        'response_type': 'code',
        'state': state,
        'scope': settings.LINKCS_SCOPE,
    }
    url = f'{AUTH_AUTHORIZE_URL}?{urlencode(body)}'.replace('%', r'%%')

    def get(self, request, *args, **kwargs):
        request.session['state'] = self.state
        request.session['next'] = self.get_success_url() or ''
        return super().get(self, request, *args, **kwargs)

    def get_success_url(self):
        url = LoginView.get_redirect_url(self)
        if hasattr(settings, 'LOGIN_LINKCS_REDIRECT_URL'):
            settings_url = settings.LOGIN_LINKCS_REDIRECT_URL
        else:
            settings_url = settings.LOGIN_REDIRECT_URL
        return url or resolve_url(settings_url)


class LinkCSRedirect(HandleGatewayErrorMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        user = authenticate(
            self.request, code=self.request.GET.get('code'),
            state=self.request.GET.get('state'))
        if user is not None:
            if not isinstance(user, AnonymousUser):
                login(self.request, user)
            return self.request.session.pop('next')

        return reverse('login')

    def handle_bad_request(self, request, **kwargs):
        logger.error('Oauth request raised an HTTP error code, this is not supposed to happen.')
        return HttpResponseServiceUnavailable()

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except RequestException as e:
            self.handle_gateway_error(e, request, *args, **kwargs)


class UserLinkCSMixin(UserPassesTestMixin):

    def test_func(self):
        if hasattr(self, 'request'):
            request = self.request
        else:
            raise ImproperlyConfigured("This Mixin should be used with a View class.")
        perm_name = f'{UserModel._meta.label}.request_linkcs'
        return ((request.user.has_perm(perm_name) and not request.user.is_superuser)
                or hasattr(request.user, 'profile')
                or request.user.username
                or 'linkcs' in request.session.keys())


class UserNotLinkCSMixin(UserLinkCSMixin):

    def test_func(self):
        return not super().test_func()


class PasswordChangeView(UserNotLinkCSMixin, PasswordChangeView):
    pass


class LoginChoiceView(TemplateView):
    template_name = 'registration/login_choice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        body = self.request.GET.urlencode(safe='/')
        body_string = f'?{body}' if body else ''
        context.update({
            'login_linkcs_url': reverse('login_linkcs') + body_string,
            'login_credentials_url': reverse('login_credentials') + body_string
        })
        return context


class GraphQLMixin(UserLinkCSMixin, HandleGatewayErrorMixin):
    query = r'{}'
    variables = r'{}'
    base_url = LINKCS_API_URL

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except RequestException as e:
            self.handle_gateway_error(e, request, **kwargs)

    def get_query(self):
        assert self.query is not None, (
            f"{self.__class__.__name__} should either include a `query`"
            "attribute, or overwrite the `get_query()` method."
        )
        return self.query

    def get_variables(self):
        assert self.variables is not None, (
            f"{self.__class__.__name__} should either include a `variables`"
            "attribute, or overwrite the `get_variables()` method."
        )
        return self.variables

    # Method to override instead of `result()`. To prevent caching,
    # use `del self.result`. If this method is not overridden,
    # `self.result` can be used.
    def get_result(self):
        return self.result

    @cached_property
    def result(self):
        if hasattr(self, 'request'):
            request = self.request
        else:
            raise ImproperlyConfigured("This Mixin should be used with a View class.")
        if 'access_token' not in request.session.keys():
            raise InvalidSessionKey
        else:
            now_timestamp = datetime.timestamp(datetime.now())
            if request.session['expires_at'] < now_timestamp:
                raise ImproperlyConfigured('Access token refreshing should be '
                                           + 'handled by a middleware')
        graphql_request = server_request_wrapper(get, self.base_url, headers={
            'Authorization':
                f"Bearer {request.session['access_token']}"
        }, params={
            'query': self.get_query(),
            'variables': self.get_variables()
        })
        return graphql_request.json()


class GraphQLView(GraphQLMixin, View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(self.get_result())
