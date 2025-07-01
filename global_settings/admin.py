from django.contrib import admin
from .models import (
    Currency,
    PaymentTerms,
    CompanyInfo,
    Localization,
    Accounting,
    UserSettings,
    EmailSettings,
    TaxSettings,
    PaymentSettings,
    BackupSettings,
    GeneralSettings,
    Notification,
)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "symbol", "exchange_rate")

@admin.register(PaymentTerms)
class PaymentTermsAdmin(admin.ModelAdmin):
    list_display = ("name", "days", "discount_percentage")

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number")

@admin.register(Localization)
class LocalizationAdmin(admin.ModelAdmin):
    list_display = ("language", "time_zone", "date_format", "decimal_separator")

@admin.register(Accounting)
class AccountingAdmin(admin.ModelAdmin):
    list_display = ("fiscal_year_start", "fiscal_year_end", "default_accounting_period", "default_journal")

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("default_role", "authentication_method")

@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ("smtp_server", "smtp_port", "sender_email")

@admin.register(TaxSettings)
class TaxSettingsAdmin(admin.ModelAdmin):
    list_display = ("tax_type", "default_tax_rate")

@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ("default_payment_method", "payment_gateway")

@admin.register(BackupSettings)
class BackupSettingsAdmin(admin.ModelAdmin):
    list_display = ("backup_frequency", "backup_location", "encryption_enabled")

@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ("system_name", "maintenance_mode", "support_email")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "notification_type", "is_read", "created_at", "all_users")
    list_filter = ("notification_type", "is_read", "all_users", "created_at")
    search_fields = ("title", "message", "recipient__username")
