from django.apps import AppConfig

class SalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Sales"

    def ready(self):
        import Sales.signals  # Ensure signals are loaded when the app starts
