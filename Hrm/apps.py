from django.apps import AppConfig


class HrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hrm'

    def ready(self):
        # Import signals
        import Hrm.signals