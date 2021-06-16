from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import AnonymousUser

from . import authenticate_server, get_linkcs_user

UserModel = get_user_model()


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
            defaults=self.get_defaults(request, user_request))
