# sales/forms/delivery_forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from ..models import Delivery, DeliveryLine, SalesOrder, SalesOrderLine, SalesEmployee
from Inventory.models import Item, Warehouse
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class DeliveryForm(forms.ModelForm):
    """Form for creating and updating Delivery records"""
    
    class Meta:
        model = Delivery
        fields = [
            'document_date', 'posting_date', 'customer', 
            'sales_order', 'status', 'sales_employee', 'deliveryemployee','delivery_method', 'driver_name', 'vehicle_number',
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
            'deliveryemployee': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            }, choices=[
                ('', ''),
                ('Car', 'Car'),
                ('Lorry', 'Lorry'),
                ('Van', 'Van'),
                ('Bike', 'Bike'),
                ('Other', 'Other'),
            ]),
            'driver_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'vehicle_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'expected_delivery_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'actual_delivery_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'tracking_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
            'delivery_notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Additional delivery notes',
            }),
            'delivery_area': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Default date & status for new record
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['posting_date'] = today
            self.initial['status'] = 'Open'

        # Filter sales_order by customer
        self._setup_sales_order_field()
        
        # Setup sales employee based on current user
        self._setup_sales_employee()

    def _setup_sales_order_field(self):
        """Setup sales_order field based on customer selection"""
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['sales_order'].queryset = SalesOrder.objects.filter(
                    customer_id=customer_id
                ).exclude(status__in=['Cancelled', 'Closed'])
            except (ValueError, TypeError):
                self.fields['sales_order'].queryset = SalesOrder.objects.none()
        elif self.instance.pk and self.instance.customer:
            self.fields['sales_order'].queryset = SalesOrder.objects.filter(
                customer=self.instance.customer
            ).exclude(status__in=['Cancelled', 'Closed'])
        elif 'sales_order' in self.initial:
            sales_order_id = self.initial['sales_order']
            self.fields['sales_order'].queryset = SalesOrder.objects.filter(id=sales_order_id)
            self.fields['sales_order'].initial = sales_order_id
        else:
            self.fields['sales_order'].queryset = SalesOrder.objects.none()

    def _setup_sales_employee(self):
        """Setup sales_employee and deliveryemployee based on current user"""
        if self.request and self.request.user.is_authenticated:
            if not self.request.user.is_superuser:
                try:
                    sales_employee = SalesEmployee.objects.get(user=self.request.user, is_active=True)
                    self.fields['sales_employee'].initial = sales_employee
                    self.fields['sales_employee'].widget.attrs['readonly'] = True
                    self.fields['deliveryemployee'].initial = self.request.user.username
                except SalesEmployee.DoesNotExist:
                    self.fields['deliveryemployee'].initial = self.request.user.username
            else:
                self.fields['deliveryemployee'].widget.attrs.pop('readonly', None)

            if not self.request.user.is_superuser:
                self.fields['deliveryemployee'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set deliveryemployee from current user if not superuser
        if self.request and self.request.user.is_authenticated and not self.request.user.is_superuser:
            instance.deliveryemployee = self.request.user.username

        if commit:
            instance.save()
        return instance

class DeliveryExtraInfoForm(forms.ModelForm):
    """Form for managing additional information for Delivery"""
    
    class Meta:
        model = Delivery
        fields = [
            'contact_person', 'shipping_address', 
            'total_amount', 'discount_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method',
            'payment_reference', 'payment_date', 'remarks'
        ]
        widgets = {
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
        
        # Set initial values for financial fields
        self._set_initial_values()
        
        # Make calculated fields read-only
        self._set_readonly_fields()
        
        # Filter contact persons and shipping addresses by customer
        self._setup_customer_related_fields()
    
    def _set_initial_values(self):
        """Set initial values for financial fields"""
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
    
    def _set_readonly_fields(self):
        """Make calculated fields read-only"""
        readonly_fields = ['total_amount', 'payable_amount', 'due_amount']
        for field in readonly_fields:
            if field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
    
    def _setup_customer_related_fields(self):
        """Filter contact persons and shipping addresses by customer"""
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=customer_id
                )
                self.fields['shipping_address'].queryset = Address.objects.filter(
                    business_partner_id=customer_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.customer:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.customer
            )
            self.fields['shipping_address'].queryset = Address.objects.filter(
                business_partner=self.instance.customer
            )
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
            self.fields['shipping_address'].queryset = Address.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Calculate financial values
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

class DeliveryLineForm(forms.ModelForm):
    """Form for Delivery Line items"""

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
        model = DeliveryLine
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
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Make unit_price read-only for non-superusers
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

# Create formset for DeliveryLine
DeliveryLineFormSet = inlineformset_factory(
    Delivery,
    DeliveryLine,
    form=DeliveryLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Add a wrapper function to pass request to the formset
def get_delivery_line_formset(request=None):
    """
    Returns a formset class with the request passed to each form
    """
    if request:
        class RequestFormSet(DeliveryLineFormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet
    
    return DeliveryLineFormSet

class DeliveryFilterForm(BaseFilterForm):
    """
    Filter form for Delivery.
    """
    MODEL_STATUS_CHOICES = Delivery.STATUS_CHOICES