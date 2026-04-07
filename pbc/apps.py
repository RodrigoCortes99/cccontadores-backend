from django.apps import AppConfig


class PbcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pbc"

    def ready(self):
        import pbc.signals  # noqa
