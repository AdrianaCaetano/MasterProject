from django.apps import AppConfig


class CarpoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'carpool'

    # def ready(self):
    #     from . import signals