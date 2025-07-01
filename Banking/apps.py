from django.apps import AppConfig


class BankingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Banking'
    
    def ready(self):
        import Banking.signals.payment_signals
        # Register signals for SalesOrderLine after all apps are ready
        Banking.signals.payment_signals.register_sales_order_line_signals()
