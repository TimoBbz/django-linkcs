from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import AnonymousUser

from . import authenticate_server, get_linkcs_user, get_profile_model, logger
from .models import LinkCSProfile

ProfileModel = get_profile_model() or LinkCSProfile


# Exceptions handlers

class LogExceptionMixin:

    @staticmethod
    def handle_exception(e):
        logger.error(getattr(e, 'message', repr(e)))
        return None


class CrashOnExceptionMixin:

    @staticmethod
    def handle_exception(e):
        raise e


# Backends

class SessionOnlyOauthBackend(LogExceptionMixin, BaseBackend):

    def fill_session(self, request):
        try:
            user_request = get_linkcs_user(request)
        except Exception as e:
            self.handle_exception(e)
            return None
        request.session.update({'linkcs': user_request})
        return request

    def authenticate(self, request, **credentials):
        if authenticate_server(request, **credentials):
            request = self.fill_session(request)
            return AnonymousUser()
        return None

    def get_user(self, user_id):
        return AnonymousUser()


class UserOauthBackend(LogExceptionMixin, ModelBackend):

    def authenticate(self, request, **credentials):
        if not authenticate_server(request, **credentials):
            return None

        try:
            user_request = get_linkcs_user(request)
        except Exception as e:
            self.handle_exception(e)
            return None

        try:
            return ProfileModel.objects.get(linkcs_id=user_request['id'])
        except ProfileModel.DoesNotExist:
            return None
        except Exception as e:
            self.handle_exception(e)


class CreateUserOauthBackend(CrashOnExceptionMixin, ModelBackend):

    def get_matching_user(self, request, user_request):
        username = user_request['login']
        if len(matching_users := ProfileModel.objects.filter(username__startswith=username)) > 0:
            i = 1
            while len(matching_users.filter(username=username + str(i))) > 0:
                i += 1
            defaults = self.get_defaults(request, user_request)
            defaults['username'] = username + str(i)
            return ProfileModel(**defaults)
        return ProfileModel(**self.get_defaults(request, user_request))

    def get_defaults(self, request, user_request):
        return {
            'linkcs_id': user_request['id'],
            'username': user_request['login'],
            'first_name': user_request['firstName'],
            'last_name': user_request['lastName'],
            'email': user_request['email'],
        }

    def authenticate(self, request, **credentials):
        if not authenticate_server(request, **credentials):
            return None

        try:
            user_request = get_linkcs_user(request)
        except Exception as e:
            self.handle_exception(e)
            return None

        if len(profile_set := ProfileModel.objects.filter(linkcs_id=user_request['id'])) > 0:
            return profile_set.get()
        else:
            try:
                new_user = self.get_matching_user(request, user_request)
                new_user.save()
                return new_user
            except Exception as e:
                self.handle_exception(e)
                return None
