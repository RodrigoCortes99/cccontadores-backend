from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import DocumentoPBC


@receiver(pre_save, sender=DocumentoPBC)
def asignar_version(sender, instance: DocumentoPBC, **kwargs):
    if instance.pk:
        return

    if instance.version:
        return

    ultimo = (
        DocumentoPBC.objects.filter(solicitud=instance.solicitud)
        .order_by("-version")
        .first()
    )
    instance.version = 1 if not ultimo else ultimo.version + 1
