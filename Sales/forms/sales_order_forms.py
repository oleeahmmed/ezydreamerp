from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from ..models import SalesOrder, SalesOrderLine, SalesEmployee
from Inventory.models import Item
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class SalesOrderForm(forms.ModelForm):
    """Form for creating and updating Sales Order records"""
    
    class Meta:
        model = SalesOrder
        fields = [
            'document_date', 'delivery_date', 'customer', 
            'status', 'sales_employee','quotation'
        ]
        widgets = {
            'document_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'delivery_date': forms.DateInput(attrs={
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
            self.initial['delivery_date'] = today + timezone.timedelta(days=7)
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

class SalesOrderExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for Sales Order"""
    
    class Meta:
        model = SalesOrder
        fields = [
            'discount_amount', 'total_amount',
            'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date',
            'remarks'
        ]
        widgets = {
            # ... existing widgets ...
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
        
        # ... existing code ...
        
        # Set initial values for new fields
        if not self.instance.pk or not self.instance.paid_amount:
            self.initial['paid_amount'] = 0
        
        if not self.instance.pk or not self.instance.due_amount:
            self.initial['due_amount'] = 0
        
        # Make due_amount read-only as it is calculated
        if 'due_amount' in self.fields:
            self.fields['due_amount'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
    
        # ... existing code ...
        
        # Get values with defaults if not provided
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
    
        # Calculate payable amount
        payable_amount = cleaned_data.get('total_amount', 0) - discount_amount
        cleaned_data['payable_amount'] = payable_amount
        
        # Calculate due amount
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
    
        return cleaned_data

class SalesOrderLineForm(forms.ModelForm):
    """Form for Sales Order Line items"""

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
        model = SalesOrderLine
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
                    cleaned_data['uom'] = item.sales_uom.name
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist")

        return cleaned_data

# Create formset for SalesOrderLine
SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderLine,
    form=SalesOrderLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Add a wrapper function to pass request to the formset
def get_sales_order_line_formset(request=None, **kwargs):
    """
    Returns a formset with the request passed to each form
    """
    FormSet = SalesOrderLineFormSet
    
    if request:
        class RequestFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet(**kwargs)
    
    return FormSet(**kwargs)

class SalesOrderFilterForm(BaseFilterForm):
    """
    Filter form for Sales Order.
    """
    MODEL_STATUS_CHOICES = SalesOrder.STATUS_CHOICES

