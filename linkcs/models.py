from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import Permission

# Create your models here.


class LinkCSProfile(get_user_model()):
    linkcs_id = models.IntegerField(
        null=True,
        unique=True,
        help_text="The LinkCS id (if the user has LinkCS)",
        verbose_name="LinkCS ID"
    )

    def save(self, *args, **kwargs):
        # Si l’utilisateur a un id LinkCS, on désactive la connexion via mot de passe.
        if self.linkcs_id and self.has_usable_password():
            self.set_unusable_password()
        super(LinkCSProfile, self).save(*args, **kwargs)
        if self.linkcs_id:
            permission = Permission.objects.get(codename="request_linkcs")
            self.user_permissions.add(permission)

    class Meta:
        permissions = [
            ("request_linkcs", "Can make a request to LinkCS"),
        ]
        verbose_name = 'LinkCS profile'
        swappable = "AUTH_PROFILE_MODEL"
