from django import forms
from django.forms.models import inlineformset_factory
from .models import (
    BusinessPartnerGroup, 
    BusinessPartner, 
    FinancialInformation, 
    ContactInformation, 
    Address, 
    ContactPerson
)
from global_settings.models import PaymentTerms, Currency

# Add this import at the top of the file
import random
import string
from django.db.models import Max

class BusinessPartnerGroupForm(forms.ModelForm):
    class Meta:
        model = BusinessPartnerGroup
        fields = ['name', 'description']

class BusinessPartnerForm(forms.ModelForm):
    # Financial Information fields
    credit_limit = forms.DecimalField(
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Maximum credit allowed for this business partner"
    )
    balance = forms.DecimalField(
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Current balance"
    )
    payment_terms = forms.ModelChoiceField(
        queryset=PaymentTerms.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Contact Information fields
    phone = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mobile = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False, 
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    federal_tax_id = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Default Billing Address fields
    default_billing_street = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Street"
    )
    default_billing_city = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="City"
    )
    default_billing_state = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="State/Province"
    )
    default_billing_zip_code = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="ZIP/Postal Code"
    )
    default_billing_country = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Country"
    )
    
    # Default Shipping Address fields
    default_shipping_street = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Street"
    )
    default_shipping_city = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="City"
    )
    default_shipping_state = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="State/Province"
    )
    default_shipping_zip_code = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="ZIP/Postal Code"
    )
    default_shipping_country = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Country"
    )
    
    # Default Contact Person fields
    default_contact_name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Name"
    )
    default_contact_position = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Position"
    )
    default_contact_phone = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Phone"
    )
    default_contact_mobile = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Mobile"
    )
    default_contact_email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email"
    )
    
    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'bp_type', 'group', 'currency', 'active',
            # Financial Information fields
            'credit_limit', 'balance', 'payment_terms',
            # Contact Information fields
            'phone', 'mobile', 'email', 'website', 'federal_tax_id',
            # Default Billing Address fields
            'default_billing_street', 'default_billing_city', 'default_billing_state', 
            'default_billing_zip_code', 'default_billing_country',
            # Default Shipping Address fields
            'default_shipping_street', 'default_shipping_city', 'default_shipping_state', 
            'default_shipping_zip_code', 'default_shipping_country',
            # Default Contact Person fields
            'default_contact_name', 'default_contact_position', 'default_contact_phone', 
            'default_contact_mobile', 'default_contact_email'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bp_type': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    # Define fieldsets for the form layout
    fieldsets = [
        {
            'title': 'Basic Information',
            'description': 'Enter the basic information for the business partner',
            'icon': 'info',
            'fields': ['code', 'name', 'bp_type', 'active'],
        },
        {
            'title': 'Financial Information',
            'description': 'Financial details and payment terms',
            'icon': 'bar-chart',
            'fields': ['credit_limit', 'balance', 'payment_terms'],
        },
        {
            'title': 'Contact Information',
            'description': 'Contact details for communication',
            'icon': 'user',
            'fields': ['phone', 'mobile', 'email', 'website', 'federal_tax_id'],
        },
        {
            'title': 'Billing Address',
            'description': 'Address for billing purposes',
            'icon': 'briefcase',
            'fields': [
                'default_billing_street', 'default_billing_city', 'default_billing_state',
                'default_billing_zip_code', 'default_billing_country'
            ],
        },
        {
            'title': 'Shipping Address',
            'description': 'Address for shipping purposes',
            'icon': 'package',
            'fields': [
                'default_shipping_street', 'default_shipping_city', 'default_shipping_state',
                'default_shipping_zip_code', 'default_shipping_country'
            ],
        },
        {
            'title': 'Primary Contact',
            'description': 'Primary contact person details',
            'icon': 'user',
            'fields': [
                'default_contact_name', 'default_contact_position', 'default_contact_phone',
                'default_contact_mobile', 'default_contact_email'
            ],
        },
    ]
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        # Auto-generate unique code for new instances
        if not instance:
            self.initial['code'] = self.generate_unique_code()
        
        # If we have an instance, populate the fields from related models
        if instance:
            # Populate Financial Information fields
            try:
                financial_info = instance.financial_info
                self.initial['credit_limit'] = financial_info.credit_limit
                self.initial['balance'] = financial_info.balance
                self.initial['payment_terms'] = financial_info.payment_terms
            except (FinancialInformation.DoesNotExist, AttributeError):
                pass
            
            # Populate Contact Information fields
            try:
                contact_info = instance.contact_info
                self.initial['phone'] = contact_info.phone
                self.initial['mobile'] = contact_info.mobile
                self.initial['email'] = contact_info.email
                self.initial['website'] = contact_info.website
                self.initial['federal_tax_id'] = contact_info.federal_tax_id
            except (ContactInformation.DoesNotExist, AttributeError):
                pass
            
            # Populate Default Billing Address fields
            try:
                billing_address = instance.addresses.filter(address_type='B', is_default=True).first()
                if billing_address:
                    self.initial['default_billing_street'] = billing_address.street
                    self.initial['default_billing_city'] = billing_address.city
                    self.initial['default_billing_state'] = billing_address.state
                    self.initial['default_billing_zip_code'] = billing_address.zip_code
                    self.initial['default_billing_country'] = billing_address.country
            except (Address.DoesNotExist, AttributeError):
                pass
            
            # Populate Default Shipping Address fields
            try:
                shipping_address = instance.addresses.filter(address_type='S', is_default=True).first()
                if shipping_address:
                    self.initial['default_shipping_street'] = shipping_address.street
                    self.initial['default_shipping_city'] = shipping_address.city
                    self.initial['default_shipping_state'] = shipping_address.state
                    self.initial['default_shipping_zip_code'] = shipping_address.zip_code
                    self.initial['default_shipping_country'] = shipping_address.country
            except (Address.DoesNotExist, AttributeError):
                pass
            
            # Populate Default Contact Person fields
            try:
                contact_person = instance.contact_persons.filter(is_default=True).first()
                if contact_person:
                    self.initial['default_contact_name'] = contact_person.name
                    self.initial['default_contact_position'] = contact_person.position
                    self.initial['default_contact_phone'] = contact_person.phone
                    self.initial['default_contact_mobile'] = contact_person.mobile
                    self.initial['default_contact_email'] = contact_person.email
            except (ContactPerson.DoesNotExist, AttributeError):
                pass
    
    def generate_unique_code(self):
        """Generate a unique code for a new business partner"""
        # Try to get the highest numeric code
        prefix = "BP"
        try:
            # Find the highest numeric code
            last_bp = BusinessPartner.objects.filter(
                code__startswith=prefix
            ).aggregate(
                Max('code')
            )['code__max']
            
            if last_bp:
                # Extract the numeric part
                try:
                    last_num = int(last_bp[len(prefix):])
                    new_num = last_num + 1
                    return f"{prefix}{new_num:04d}"
                except ValueError:
                    pass
        except Exception:
            pass
        
        # Fallback: Generate a random code
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{random_part}"
    
    def save(self, commit=True):
        business_partner = super().save(commit=commit)
        
        if commit:
            # Save Financial Information
            financial_info, created = FinancialInformation.objects.get_or_create(
                business_partner=business_partner,
                defaults={
                    'credit_limit': self.cleaned_data.get('credit_limit') or 0,
                    'balance': self.cleaned_data.get('balance') or 0,
                    'payment_terms': self.cleaned_data.get('payment_terms')
                }
            )
            
            if not created:
                financial_info.credit_limit = self.cleaned_data.get('credit_limit') or 0
                financial_info.balance = self.cleaned_data.get('balance') or 0
                financial_info.payment_terms = self.cleaned_data.get('payment_terms')
                financial_info.save()
            
            # Save Contact Information
            contact_info, created = ContactInformation.objects.get_or_create(
                business_partner=business_partner,
                defaults={
                    'phone': self.cleaned_data.get('phone') or '',
                    'mobile': self.cleaned_data.get('mobile') or '',
                    'email': self.cleaned_data.get('email') or '',
                    'website': self.cleaned_data.get('website') or '',
                    'federal_tax_id': self.cleaned_data.get('federal_tax_id') or ''
                }
            )
            
            if not created:
                contact_info.phone = self.cleaned_data.get('phone') or ''
                contact_info.mobile = self.cleaned_data.get('mobile') or ''
                contact_info.email = self.cleaned_data.get('email') or ''
                contact_info.website = self.cleaned_data.get('website') or ''
                contact_info.federal_tax_id = self.cleaned_data.get('federal_tax_id') or ''
                contact_info.save()
            
            # Save Default Billing Address
            if self.cleaned_data.get('default_billing_street'):
                billing_address, created = Address.objects.get_or_create(
                    business_partner=business_partner,
                    address_type='B',
                    is_default=True,
                    defaults={
                        'street': self.cleaned_data.get('default_billing_street'),
                        'city': self.cleaned_data.get('default_billing_city') or '',
                        'state': self.cleaned_data.get('default_billing_state') or '',
                        'zip_code': self.cleaned_data.get('default_billing_zip_code') or '',
                        'country': self.cleaned_data.get('default_billing_country') or ''
                    }
                )
                
                if not created:
                    billing_address.street = self.cleaned_data.get('default_billing_street')
                    billing_address.city = self.cleaned_data.get('default_billing_city') or ''
                    billing_address.state = self.cleaned_data.get('default_billing_state') or ''
                    billing_address.zip_code = self.cleaned_data.get('default_billing_zip_code') or ''
                    billing_address.country = self.cleaned_data.get('default_billing_country') or ''
                    billing_address.save()
            
            # Save Default Shipping Address
            if self.cleaned_data.get('default_shipping_street'):
                shipping_address, created = Address.objects.get_or_create(
                    business_partner=business_partner,
                    address_type='S',
                    is_default=True,
                    defaults={
                        'street': self.cleaned_data.get('default_shipping_street'),
                        'city': self.cleaned_data.get('default_shipping_city') or '',
                        'state': self.cleaned_data.get('default_shipping_state') or '',
                        'zip_code': self.cleaned_data.get('default_shipping_zip_code') or '',
                        'country': self.cleaned_data.get('default_shipping_country') or ''
                    }
                )
                
                if not created:
                    shipping_address.street = self.cleaned_data.get('default_shipping_street')
                    shipping_address.city = self.cleaned_data.get('default_shipping_city') or ''
                    shipping_address.state = self.cleaned_data.get('default_shipping_state') or ''
                    shipping_address.zip_code = self.cleaned_data.get('default_shipping_zip_code') or ''
                    shipping_address.country = self.cleaned_data.get('default_shipping_country') or ''
                    shipping_address.save()
            
            # Save Default Contact Person
            if self.cleaned_data.get('default_contact_name'):
                contact_person, created = ContactPerson.objects.get_or_create(
                    business_partner=business_partner,
                    is_default=True,
                    defaults={
                        'name': self.cleaned_data.get('default_contact_name'),
                        'position': self.cleaned_data.get('default_contact_position') or '',
                        'phone': self.cleaned_data.get('default_contact_phone') or '',
                        'mobile': self.cleaned_data.get('default_contact_mobile') or '',
                        'email': self.cleaned_data.get('default_contact_email') or ''
                    }
                )
                
                if not created:
                    contact_person.name = self.cleaned_data.get('default_contact_name')
                    contact_person.position = self.cleaned_data.get('default_contact_position') or ''
                    contact_person.phone = self.cleaned_data.get('default_contact_phone') or ''
                    contact_person.mobile = self.cleaned_data.get('default_contact_mobile') or ''
                    contact_person.email = self.cleaned_data.get('default_contact_email') or ''
                    contact_person.save()
        
        return business_partner

# Keep the original forms for backward compatibility
class FinancialInformationForm(forms.ModelForm):
    business_partner = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_terms = forms.ModelChoiceField(
        queryset=PaymentTerms.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = FinancialInformation
        fields = ['business_partner', 'credit_limit', 'balance', 'payment_terms']
        widgets = {
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ContactInformationForm(forms.ModelForm):
    business_partner = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = ContactInformation
        fields = ['business_partner', 'phone', 'mobile', 'email', 'website', 'federal_tax_id']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'federal_tax_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AddressForm(forms.ModelForm):
    business_partner = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Address
        fields = ['business_partner', 'address_type', 'street', 'city', 'state', 'zip_code', 'country', 'is_default']
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContactPersonForm(forms.ModelForm):
    business_partner = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = ContactPerson
        fields = ['business_partner', 'name', 'position', 'phone', 'mobile', 'email', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BusinessPartnerFilterForm(forms.Form):
    bp_type = forms.ChoiceField(
        choices=[('', 'All')] + BusinessPartner.BP_TYPES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ModelChoiceField(
        queryset=BusinessPartnerGroup.objects.all(), 
        required=False, 
        empty_label="All Groups",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'})
    )

# Create formsets for related models
AddressFormSet = inlineformset_factory(
    BusinessPartner, 
    Address, 
    form=AddressForm, 
    extra=1, 
    can_delete=True
)

ContactPersonFormSet = inlineformset_factory(
    BusinessPartner, 
    ContactPerson, 
    form=ContactPersonForm, 
    extra=1, 
    can_delete=True
)