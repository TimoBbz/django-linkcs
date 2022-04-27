from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend, ModelBackend
from django.contrib.auth.models import AnonymousUser

from . import authenticate_server, get_linkcs_user, get_profile_model, logger

UserModel = get_user_model()

if has_profile := hasattr(settings, "AUTH_PROFILE_MODEL"):
    ProfileModel = get_profile_model()


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

        if has_profile:
            try:
                return ProfileModel.objects.get(linkcs_id=user_request['id']).user
            except ProfileModel.DoesNotExist:
                return None
            except Exception as e:
                self.handle_exception(e)

        try:
            return UserModel.objects.get(linkcs_id=user_request['id'])
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            self.handle_exception(e)


class CreateUserOauthBackend(CrashOnExceptionMixin, ModelBackend):

    def get_matching_user(self, request, user_request):
        username = user_request['login']
        if len(matching_users := UserModel.objects.filter(username__startswith=username)) > 0:
            i = 1
            while len(matching_users.filter(username=username + str(i))) > 0:
                i += 1
            defaults = self.get_defaults(request, user_request)
            defaults['username'] = username + str(i)
            return UserModel(**defaults)
        return UserModel(**self.get_defaults(request, user_request))

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

        try:
            user_request = get_linkcs_user(request)
        except Exception as e:
            self.handle_exception(e)
            return None

        if has_profile:
            if len(profile_set := ProfileModel.objects.filter(linkcs_id=user_request['id'])) > 0:
                return profile_set.get().user
            else:
                try:
                    new_user = self.get_matching_user(request, user_request)
                    new_user.save()
                except Exception as e:
                    self.handle_exception(e)
                    return None

                profile = ProfileModel(
                    linkcs_id=user_request['id'],
                    user=new_user)
                profile.save()
                return new_user

        else:
            try:
                return UserModel.objects.get_or_create(
                    linkcs_id=user_request['id'],
                    defaults=self.get_defaults(request, user_request))[0]
            except Exception as e:
                self.handle_exception(e)
