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
        fields = [
            # Basic Info
            'name', 'legal_name', 'tagline', 'description',

            # Contact
            'email', 'phone_number', 'alternate_phone', 'website',

            # Address
            'address', 'address_line2', 'city', 'state', 'postal_code', 'country',

            # Registration
            'registration_number', 'tax_id', 'vat_number', 'tax_info',

            # Branding
            'logo', 'favicon',

            # Fiscal
            'default_currency', 'fiscal_year_start', 'fiscal_year_end',
            'timezone', 'language',

            # Social
            'facebook_url', 'linkedin_url', 'instagram_url', 'twitter_url',

            # Status
            'is_active',
        ]
        widgets = {
            # Basic Info
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Company Name'
            }),
            'legal_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Legal Name'
            }),
            'tagline': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Tagline'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'rows': 2,
                'placeholder': 'Company Description'
            }),

            # Contact
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Email Address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Phone Number'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Alternate Phone'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Website URL'
            }),

            # Address
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'rows': 2,
                'placeholder': 'Address Line 1'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Address Line 2'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Country'
            }),

            # Registration & Tax
            'registration_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Registration Number'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Tax ID'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'VAT Number'
            }),
            'tax_info': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'rows': 2,
                'placeholder': 'Tax Details'
            }),

            # Fiscal
            'fiscal_year_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700'
            }),
            'fiscal_year_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700'
            }),
            'default_currency': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Currency (e.g., USD)'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Time Zone (e.g., UTC)'
            }),
            'language': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Language (e.g., en)'
            }),

            # Social
            'facebook_url': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Facebook URL'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'LinkedIn URL'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Instagram URL'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Twitter URL'
            }),

            # Logo & Favicon
            'logo': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700'
            }),
            'favicon': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700'
            }),

            # Status
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 border border-gray-300 rounded text-blue-600 focus:ring-blue-500'
            }),
        }
        # Fieldsets for UI layout
        fieldsets = [
            {
                'title': 'Basic Details',
                'description': 'Primary company identity and slogan',
                'icon': 'building',
                'fields': ['name', 'legal_name', 'tagline', 'description'],
            },
            {
                'title': 'Contact Information',
                'description': 'Communication details',
                'icon': 'phone',
                'fields': ['email', 'phone_number', 'alternate_phone', 'website'],
            },
            {
                'title': 'Address',
                'description': 'Physical company location',
                'icon': 'map-pin',
                'fields': ['address', 'address_line2', 'city', 'state', 'postal_code', 'country'],
            },
            {
                'title': 'Registration & Tax',
                'description': 'Legal and taxation identifiers',
                'icon': 'briefcase',
                'fields': ['registration_number', 'tax_id', 'vat_number', 'tax_info'],
            },
            {
                'title': 'Branding',
                'description': 'Visual identity elements',
                'icon': 'image',
                'fields': ['logo', 'favicon'],
            },
            {
                'title': 'Localization Settings',
                'description': 'Currency, timezone, and fiscal period settings',
                'icon': 'globe',
                'fields': ['default_currency', 'fiscal_year_start', 'fiscal_year_end', 'timezone', 'language'],
            },
            {
                'title': 'Social Media',
                'description': 'Company’s social presence',
                'icon': 'share-2',
                'fields': ['facebook_url', 'linkedin_url', 'instagram_url', 'twitter_url'],
            },
            {
                'title': 'Status',
                'description': 'Toggle visibility/activation',
                'icon': 'toggle-left',
                'fields': ['is_active'],
            },
        ]
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