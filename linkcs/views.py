from random import choice
from requests import get
from string import ascii_letters
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic.base import RedirectView, View
from django.shortcuts import redirect

from . import AUTH_AUTHORIZE_URL, LINKCS_API_URL

# Login


class LinkCSLogin(RedirectView):
    
    state = ''.join(choice(ascii_letters) for _ in range(10))
    body = {
        'redirect_uri':settings.REDIRECT_URI,
        'client_id':settings.CLIENT_ID,
        'response_type':'code',
        'state':state,
        'scope':settings.LINKCS_SCOPE,
    }

    url = f'{AUTH_AUTHORIZE_URL}?{urlencode(body)}'.replace('%', r'%%')

    def get(self, request, *args, **kwargs):
        request.session['state'] = self.state
        return super().get(self, request, *args, **kwargs)


class LinkCSRedirect(View):

    def get(self, request, *args, **kwargs):
        user = authenticate(request, code=request.GET.get('code'), state=request.GET.get('state'))
        if user is not None:
            login(request, user)
        return redirect('/rest/users')

            

# Fetch LinkCS:


class GraphQLView(View):

    query = r'{}'
    base_url = LINKCS_API_URL

    def get_query(self, request):
        assert self.query is not None, (
            f"{self.__class__.__name__} should either include a `query`"
            "attribute, or overwrite the `get_query()` method."  
        )

        return self.query

    def get(self, request):

        if 'access_token' not in request.session.keys() or 'expires_at' not in request.session.keys():
            return HttpResponseForbidden()

        graphql_request = get(self.base_url, headers={
            'Authorization': f"Bearer {request.session['access_token']}"
        }, params={
            'query': self.get_query(request)
        })

        return JsonResponse(graphql_request.json())