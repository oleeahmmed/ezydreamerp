from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from ..models import Return, ReturnLine, Delivery, DeliveryLine, SalesEmployee
from Inventory.models import Item, Warehouse
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class ReturnForm(forms.ModelForm):
    """Form for creating and updating Return records"""
    
    class Meta:
        model = Return
        fields = [
            'document_date', 'posting_date', 'customer', 
            'delivery', 'status', 'sales_employee',
        ]
        widgets = {
            'document_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'posting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'delivery': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'customer': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'sales_employee': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        
        # Get initial data before calling super
        initial = kwargs.get('initial', {})
        
        # Call super after setting initial
        super().__init__(*args, **kwargs)
        
        # Respect initial data from prefill if provided
        if initial.get('document_date'):
            self.fields['document_date'].initial = initial['document_date']
        if initial.get('posting_date'):
            self.fields['posting_date'].initial = initial['posting_date']
        
        # Set default values only if not provided in initial data
        if not self.instance.pk and not initial.get('document_date'):
            self.fields['document_date'].initial = timezone.now().date()
        if not self.instance.pk and not initial.get('posting_date'):
            self.fields['posting_date'].initial = timezone.now().date()
        if not self.instance.pk and not initial.get('status'):
            self.fields['status'].initial = 'Open'
        
        # Show all deliveries instead of filtering by customer
        self.fields['delivery'].queryset = Delivery.objects.filter(
            status__in=['Delivered', 'Partially Delivered', 'Open', 'Draft']
        ).order_by('-id')  # Show newest deliveries first
        
        # If we have a specific delivery ID in initial data, make sure it's selected
        delivery_id = initial.get('delivery')
        if delivery_id:
            try:
                delivery = Delivery.objects.get(id=delivery_id)
                self.fields['delivery'].initial = delivery_id
            except Delivery.DoesNotExist:
                pass
        
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

class ReturnExtraInfoForm(forms.ModelForm):
    """Form for managing additional information for Return"""
    
    class Meta:
        model = Return
        fields = [
            'contact_person', 'return_address', 'currency', 'payment_terms',
            'total_amount', 'discount_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method',
            'payment_reference', 'payment_date',
            'return_reason', 'remarks'
        ]
        widgets = {
            'return_reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'peer w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Return Reason',
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 4,
                'class': 'peer w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Remarks',
            }),
            'total_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'readonly': 'readonly',
            }),
            'discount_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
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
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            }, choices=[
                ('', ''),
                ('Cash', 'Cash'),
                ('Bank Transfer', 'Bank Transfer'),
                ('Credit Card', 'Credit Card'),
                ('Check', 'Check'),
                ('Online Payment', 'Online Payment'),
                ('Other', 'Other'),
            ]),
            'payment_reference': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'placeholder': 'Payment Reference',
            }),
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if not self.instance.pk or not self.instance.total_amount:
            self.initial['total_amount'] = 0
            
        if not self.instance.pk or not self.instance.discount_amount:
            self.initial['discount_amount'] = 0
            
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
            
        # Filter contact persons by customer if customer is selected
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=customer_id
                )
                self.fields['return_address'].queryset = Address.objects.filter(
                    business_partner_id=customer_id
                )
                
                # Try to get default values from customer
                try:
                    customer = BusinessPartner.objects.get(id=customer_id)
                    if customer.currency and not self.instance.currency:
                        self.initial['currency'] = customer.currency
                    if customer.payment_terms and not self.instance.payment_terms:
                        self.initial['payment_terms'] = customer.payment_terms
                except BusinessPartner.DoesNotExist:
                    pass
                    
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.customer:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.customer
            )
            self.fields['return_address'].queryset = Address.objects.filter(
                business_partner=self.instance.customer
            )
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
            self.fields['return_address'].queryset = Address.objects.none()
            
    def clean(self):
        cleaned_data = super().clean()
        
        # Get values with defaults if not provided
        total_amount = cleaned_data.get('total_amount', 0) or 0
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
        
        # Calculate payable amount
        payable_amount = total_amount - discount_amount
        cleaned_data['payable_amount'] = payable_amount
        
        # Calculate due amount
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
        
        return cleaned_data

class ReturnLineForm(forms.ModelForm):
    """Form for Return Line items"""

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
        model = ReturnLine
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
                if not cleaned_data.get('uom') and item.inventory_uom:
                    cleaned_data['uom'] = item.inventory_uom.code
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist")

        return cleaned_data

# Create formset for ReturnLine
ReturnLineFormSet = inlineformset_factory(
    Return,
    ReturnLine,
    form=ReturnLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Add a wrapper function to pass request to the formset
def get_return_line_formset(request=None, **kwargs):
    """
    Returns a formset with the request passed to each form
    """
    FormSet = ReturnLineFormSet
    
    if request:
        class RequestFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet(**kwargs)
    
    return FormSet(**kwargs)

class ReturnFilterForm(BaseFilterForm):
    """
    Filter form for Return.
    """
    MODEL_STATUS_CHOICES = Return.STATUS_CHOICES