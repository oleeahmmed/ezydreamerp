from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from ..models import SalesQuotation, SalesQuotationLine, SalesEmployee
from Inventory.models import Item
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm


class SalesQuotationForm(forms.ModelForm):
    """Form for creating and updating Sales Quotation records"""
    
    class Meta:
        model = SalesQuotation
        fields = [
            'document_date', 'customer', 
            'status', 'sales_employee',
        ]
        widgets = {
            'document_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'valid_until': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for date fields
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['valid_until'] = today + timezone.timedelta(days=30)
            self.initial['status'] = 'Open'
        
        # Handle sales employee auto-selection based on current user
        if self.request and self.request.user.is_authenticated:
            # If user is not a superuser and has a linked sales employee, set it as default
            if not self.request.user.is_superuser:
                try:
                    sales_employee = SalesEmployee.objects.get(user=self.request.user, is_active=True)
                    self.fields['sales_employee'].initial = sales_employee
                    self.fields['sales_employee'].widget.attrs['readonly'] = True
                except SalesEmployee.DoesNotExist:
                    pass


class SalesQuotationExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for Sales Quotation"""
    
    class Meta:
        model = SalesQuotation
        fields = [
            'contact_person', 'billing_address', 'shipping_address',
            'currency', 'payment_terms', 'discount_amount', 'total_amount',
            'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date',
            'remarks'
        ]
        widgets = {
            'remarks': forms.Textarea(attrs={
                'rows': 4,
                'class': 'peer w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Remarks',
            }),
            'discount_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
            }),
            'total_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'readonly': 'readonly',
            }),
            'payable_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'readonly': 'readonly',
            }),
            'paid_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
            }),
            'due_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'readonly': 'readonly',
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))]',
                'placeholder': 'Payment Method',
            }),
            'payment_reference': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))]',
                'placeholder': 'Payment Reference',
            }),
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))]',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values of 0 for financial fields if they're empty
        if not self.instance.pk or not self.instance.discount_amount:
            self.initial['discount_amount'] = 0
        
        if not self.instance.pk or not self.instance.total_amount:
            self.initial['total_amount'] = 0
        
        if not self.instance.pk or not self.instance.payable_amount:
            self.initial['payable_amount'] = 0
        
        if not self.instance.pk or not self.instance.paid_amount:
            self.initial['paid_amount'] = 0
        
        if not self.instance.pk or not self.instance.due_amount:
            self.initial['due_amount'] = 0
    
        # Make some fields read-only as they are calculated
        if 'total_amount' in self.fields:
            self.fields['total_amount'].widget.attrs['readonly'] = True
            
        if 'payable_amount' in self.fields:
            self.fields['payable_amount'].widget.attrs['readonly'] = True
            
        if 'due_amount' in self.fields:
            self.fields['due_amount'].widget.attrs['readonly'] = True
            
        # Filter contact persons and addresses by customer if customer is selected
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=customer_id
                )
                self.fields['billing_address'].queryset = Address.objects.filter(
                    business_partner_id=customer_id,
                    address_type='B'
                )
                self.fields['shipping_address'].queryset = Address.objects.filter(
                    business_partner_id=customer_id,
                    address_type='S'
                )
                
                # Try to get default values from customer
                try:
                    customer = BusinessPartner.objects.get(id=customer_id)
                    if customer.currency and not self.instance.currency:
                        self.initial['currency'] = customer.currency
                    if customer.payment_terms and not self.instance.payment_terms:
                        self.initial['payment_terms'] = customer.payment_terms
                    
                    # Set default contact person
                    default_contact = customer.contact_persons.filter(is_default=True).first()
                    if default_contact and not self.instance.contact_person:
                        self.initial['contact_person'] = default_contact
                        
                    # Set default billing address
                    default_billing = customer.addresses.filter(address_type='B', is_default=True).first()
                    if default_billing and not self.instance.billing_address:
                        self.initial['billing_address'] = default_billing
                        
                    # Set default shipping address
                    default_shipping = customer.addresses.filter(address_type='S', is_default=True).first()
                    if default_shipping and not self.instance.shipping_address:
                        self.initial['shipping_address'] = default_shipping
                except BusinessPartner.DoesNotExist:
                    pass
                
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.customer:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.customer
            )
            self.fields['billing_address'].queryset = Address.objects.filter(
                business_partner=self.instance.customer,
                address_type='B'
            )
            self.fields['shipping_address'].queryset = Address.objects.filter(
                business_partner=self.instance.customer,
                address_type='S'
            )
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
            self.fields['billing_address'].queryset = Address.objects.none()
            self.fields['shipping_address'].queryset = Address.objects.none()

    def clean(self):
        cleaned_data = super().clean()
    
        # Handle missing financial fields by providing default values
        financial_fields = [
            'discount_amount', 'total_amount',
            'payable_amount', 'paid_amount', 'due_amount'
        ]
    
        for field in financial_fields:
            if field not in cleaned_data:
                cleaned_data[field] = 0
    
        # Get values with defaults if not provided
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
    
        # Calculate payable amount (now directly from total_amount)
        payable_amount = cleaned_data.get('total_amount', 0) - discount_amount
        cleaned_data['payable_amount'] = payable_amount
    
        # Calculate due amount
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
    
        return cleaned_data


class SalesQuotationLineForm(forms.ModelForm):
    """Form for Sales Quotation Line items"""

    item_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 item-code-autocomplete',
            'placeholder': 'Enter item code',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = SalesQuotationLine
        fields = [
            'item_code', 'item_name', 'quantity', 'unit_price', 'uom', 'remarks', 'is_active'
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Item name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'step': '1',
                'min': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'step': '0.000001',
                'min': '0'
            }),
            'uom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Unit of measure'
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Remarks',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 border border-gray-300 rounded text-blue-600 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Make unit_price read-only if user is not a superuser
        if self.request and self.request.user.is_authenticated and not self.request.user.is_superuser:
            if 'unit_price' in self.fields:
                self.fields['unit_price'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        item_code = cleaned_data.get('item_code')

        # Validate item selection
        if not item_code:
            self.add_error('item_code', 'Item code is required')
        else:
            try:
                item = Item.objects.get(code=item_code)
                if not cleaned_data.get('item_name'):
                    cleaned_data['item_name'] = item.name
                if not cleaned_data.get('uom') and item.sales_uom:
                    cleaned_data['uom'] = item.sales_uom.code
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist")

        return cleaned_data


# Create formset for SalesQuotationLine
SalesQuotationLineFormSet = inlineformset_factory(
    SalesQuotation,
    SalesQuotationLine,
    form=SalesQuotationLineForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)

# Add a wrapper function to pass request to the formset
def get_sales_quotation_line_formset(request=None, **kwargs):
    """
    Returns a formset with the request passed to each form
    """
    FormSet = SalesQuotationLineFormSet
    
    if request:
        class RequestFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet(**kwargs)
    
    return FormSet(**kwargs)

class SalesQuotationFilterForm(BaseFilterForm):
    """
    Filter form for Sales Quotation.
    """
    MODEL_STATUS_CHOICES = SalesQuotation.STATUS_CHOICES

