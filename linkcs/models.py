from django.db import models
from django.contrib.auth.models import AbstractUser, Permission

# Create your models here.


class AbstractLinkcsUser(AbstractUser):

    linkcs_id = models.IntegerField(
        null=True,
        unique=True,
        help_text="The LinkCS id (if the user has LinkCS)",
        verbose_name="LinkCS ID"
    )

    class Meta(AbstractUser.Meta):
        abstract = True
        permissions = [
            ("request_linkcs", "Can make a request to LinkCS"),
        ]

    def save(self, *args, **kwargs):
        # Si l’utilisateur a un id LinkCS, on désactive la connexion
        # via mot de passe.
        if self.linkcs_id and self.has_usable_password():
            self.set_unusable_password()
        super().save(*args, **kwargs)
        if self.linkcs_id:
            permission = Permission.objects.get(codename="request_linkcs")
            self.user_permissions.add(permission)
