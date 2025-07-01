from django.db import models
from django.contrib.auth.models import User

# Currency Settings
class Currency(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return self.name
        
class PaymentTerms(models.Model):
    name = models.CharField(max_length=50, unique=True)
    days = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.name


# Company Information

class CompanyInfo(models.Model):
    # Basic Info
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Contact Info
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Address Info
    address = models.TextField()
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Registration & Tax Info
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    vat_number = models.CharField(max_length=100, blank=True, null=True)
    tax_info = models.TextField(blank=True, null=True)

    # Branding
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='company_favicons/', blank=True, null=True)

    # Fiscal & Locale Settings
    default_currency = models.CharField(max_length=10, default='USD')
    fiscal_year_start = models.DateField(blank=True, null=True)
    fiscal_year_end = models.DateField(blank=True, null=True)
    timezone = models.CharField(max_length=100, default='UTC')
    language = models.CharField(max_length=50, default='en')

    # Social Media
    facebook_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)

    # Active flag
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.name


# Localization Settings
class Localization(models.Model):
    time_zone = models.CharField(max_length=50)
    language = models.CharField(max_length=50)
    date_format = models.CharField(max_length=20)
    time_format = models.CharField(max_length=20)
    decimal_separator = models.CharField(max_length=1)
    thousand_separator = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.language} - {self.time_zone}"

# Accounting Settings
class Accounting(models.Model):
    fiscal_year_start = models.DateField()
    fiscal_year_end = models.DateField()
    default_accounting_period = models.CharField(max_length=20)
    default_journal = models.CharField(max_length=100)

    def __str__(self):
        return f"Fiscal Year: {self.fiscal_year_start.year}-{self.fiscal_year_end.year}"

        
# User Settings
class UserSettings(models.Model):
    default_role = models.CharField(max_length=100)
    default_permissions = models.JSONField()  # List of permissions like ["read", "write"]
    authentication_method = models.CharField(max_length=50)  # E.g., 'email', 'two_factor'

    def __str__(self):
        return f"User Settings for {self.default_role}"

# Email Settings
class EmailSettings(models.Model):
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.IntegerField()
    sender_email = models.EmailField()
    email_templates = models.JSONField()  # Store email templates in JSON format

    def __str__(self):
        return f"Email Settings for {self.smtp_server}"

# Tax Settings
class TaxSettings(models.Model):
    tax_type = models.CharField(max_length=50)  # e.g., VAT, GST
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2)  # For example, 15.00

    def __str__(self):
        return f"{self.tax_type} - {self.default_tax_rate}%"

# Payment Settings
class PaymentSettings(models.Model):
    supported_payment_methods = models.JSONField()  # List of payment methods like ['Credit Card', 'PayPal']
    default_payment_method = models.CharField(max_length=50)
    payment_gateway = models.CharField(max_length=100)  # E.g., 'Stripe', 'PayPal'

    def __str__(self):
        return f"Default Payment Method: {self.default_payment_method}"

# Backup Settings
class BackupSettings(models.Model):
    backup_frequency = models.CharField(max_length=50)  # E.g., 'daily', 'weekly'
    backup_location = models.CharField(max_length=255)  # Local path or cloud location
    encryption_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Backup Frequency: {self.backup_frequency}"

# General Settings
class GeneralSettings(models.Model):
    system_name = models.CharField(max_length=200)
    system_description = models.TextField()
    system_logo = models.ImageField(upload_to='system_logos/')
    maintenance_mode = models.BooleanField(default=False)
    support_email = models.EmailField()

    def __str__(self):
        return f"{self.system_name} - Maintenance Mode: {'Enabled' if self.maintenance_mode else 'Disabled'}"



class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications', 
        null=True, blank=True  # User ফিল্ড Optional রাখছি
    )
    all_users = models.BooleanField(default=False)  # সকল ইউজারের জন্য নোটিফিকেশন
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.all_users:
            return f"[All Users] {self.title}"
        return f"{self.title} - {self.recipient.username if self.recipient else 'All Users'}"

    class Meta:
        ordering = ['-created_at']