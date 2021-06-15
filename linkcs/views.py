from random import choice
from requests import get
from string import ascii_letters
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, views
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.sessions.exceptions import InvalidSessionKey
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.views.generic.base import RedirectView, View, TemplateView
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from . import AUTH_AUTHORIZE_URL, AUTH_USER_URL, LINKCS_API_URL

UserModel = get_user_model()



# Auth


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
        print(request.GET)
        request.session['state'] = self.state
        request.session['next'] = self.get_success_url() or ''
        return super().get(self, request, *args, **kwargs)

    def get_success_url(self):
        url = LoginView.get_redirect_url(self)
        return url or resolve_url(settings.LOGIN_LINKCS_REDIRECT_URL or settings.LOGIN_REDIRECT_URL)


class LinkCSRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        user = authenticate(self.request, code=self.request.GET.get('code'), state=self.request.GET.get('state'))
        if user is not None:
            login(self.request, user)
            return self.request.session.pop('next')

        return reverse('login')


class UserNotLinkCSMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.has_perm(f'{UserModel._meta.label}.request_linkcs')


class PasswordChangeView(UserNotLinkCSMixin, PasswordChangeView):
    pass


class LoginChoiceView(TemplateView):

    template_name = 'registration/login_choice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        body = self.request.GET.urlencode(safe='/')
        body_string = f'?{body}' if body else ''
        if body:
            context['login_linkcs_url'] = reverse('login_linkcs') + body_string
            context['login_credentials_url'] = reverse('login_credentials') + body_string
        return context



# Fetch LinkCS:


class GraphQLMixin(PermissionRequiredMixin):

    permission_required = f'{UserModel._meta.app_label}.request_linkcs'

    query = r'{}'
    variables = r'{}'
    base_url = LINKCS_API_URL

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

    def get_graphql(self, cached=True):
        if 'access_token' not in self.request.session.keys() or 'expires_at' not in self.request.session.keys():
            raise InvalidSessionKey

        if not hasattr(self, 'graphql_result') or not cached:
            graphql_request = get(self.base_url, headers={
                'Authorization': f"Bearer {self.request.session['access_token']}"
            }, params={
                'query': self.get_query(),
                'variables': self.get_variables()
            })

            self.graphql_result = graphql_request.json()
        return self.graphql_result


class GraphQLView(GraphQLMixin, View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(self.get_graphql())
