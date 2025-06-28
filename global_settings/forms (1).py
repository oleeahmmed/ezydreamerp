from django import forms
from .models import (
    Currency, PaymentTerms, CompanyInfo, Localization, Accounting,
    UserSettings, EmailSettings, TaxSettings, PaymentSettings,
    BackupSettings, GeneralSettings,Notification
)

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['name', 'code', 'symbol', 'exchange_rate']
        widgets = {
            'exchange_rate': forms.NumberInput(attrs={'step': '0.0001'})
        }

class PaymentTermsForm(forms.ModelForm):
    class Meta:
        model = PaymentTerms
        fields = ['name', 'days', 'discount_percentage']
        widgets = {
            'discount_percentage': forms.NumberInput(attrs={'step': '0.01'})
        }

class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model = CompanyInfo
        fields = ['name', 'address', 'email', 'phone_number', 'logo', 'tax_info']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'tax_info': forms.Textarea(attrs={'rows': 3})
        }

class LocalizationForm(forms.ModelForm):
    class Meta:
        model = Localization
        fields = ['time_zone', 'language', 'date_format', 'time_format', 'decimal_separator', 'thousand_separator']
        widgets = {
            'decimal_separator': forms.TextInput(attrs={'maxlength': 1}),
            'thousand_separator': forms.TextInput(attrs={'maxlength': 1})
        }

class AccountingForm(forms.ModelForm):
    class Meta:
        model = Accounting
        fields = ['fiscal_year_start', 'fiscal_year_end', 'default_accounting_period', 'default_journal']

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['default_role', 'default_permissions', 'authentication_method']
        widgets = {
            'default_permissions': forms.Textarea(attrs={'rows': 3})
        }

class EmailSettingsForm(forms.ModelForm):
    class Meta:
        model = EmailSettings
        fields = ['smtp_server', 'smtp_port', 'sender_email', 'email_templates']
        widgets = {
            'email_templates': forms.Textarea(attrs={'rows': 3})
        }

class TaxSettingsForm(forms.ModelForm):
    class Meta:
        model = TaxSettings
        fields = ['tax_type', 'default_tax_rate']
        widgets = {
            'default_tax_rate': forms.NumberInput(attrs={'step': '0.01'})
        }

class PaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = PaymentSettings
        fields = ['supported_payment_methods', 'default_payment_method', 'payment_gateway']
        widgets = {
            'supported_payment_methods': forms.Textarea(attrs={'rows': 3})
        }

class BackupSettingsForm(forms.ModelForm):
    class Meta:
        model = BackupSettings
        fields = ['backup_frequency', 'backup_location', 'encryption_enabled']

class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = GeneralSettings
        fields = ['system_name', 'system_description', 'system_logo', 'maintenance_mode', 'support_email']
        widgets = {
            'system_description': forms.Textarea(attrs={'rows': 3})
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['recipient', 'all_users', 'title', 'message', 'notification_type', 'is_read']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }        