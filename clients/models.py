from django.conf import settings
from django.db import models


class Client(models.Model):
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="clients",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profile",
    )
    name = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, blank=True, default="")
    industry = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
