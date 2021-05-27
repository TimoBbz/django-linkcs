from django.db import models
from django.contrib.auth.models import AbstractUser

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

    def save(self, **kwargs):
        # Si l’utilisateur a un id LinkCS, on désactive la connexion via mot de passe.
        if self.linkcs_id:
            self.set_unusable_password()
        return super(AbstractLinkcsUser, self).save(**kwargs)
