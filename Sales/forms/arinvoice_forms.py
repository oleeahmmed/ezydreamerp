from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

from ..models import ARInvoice, ARInvoiceLine, SalesOrder, Delivery, SalesOrderLine, DeliveryLine, SalesEmployee
from Inventory.models import Item
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class ARInvoiceForm(forms.ModelForm):
    """Form for creating and updating AR Invoice records"""
    
    # Replace ForeignKey fields with simple number fields
    sales_order_number = forms.IntegerField(required=False, label="Sales Order #")
    delivery_number = forms.IntegerField(required=False, label="Delivery #")
    
    class Meta:
        model = ARInvoice
        fields = [
            'document_date', 'posting_date', 'due_date', 'customer', 
            'status', 'sales_employee',
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
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        instance = kwargs.get('instance')
        
        # Initialize with sales_order_number and delivery_number if instance exists
        initial = kwargs.get('initial', {})
        if instance:
            if instance.sales_order:
                initial['sales_order_number'] = instance.sales_order.id
            if instance.delivery:
                initial['delivery_number'] = instance.delivery.id
        
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        
        # Set initial values for date fields
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['posting_date'] = today
            self.initial['status'] = 'Open'
        
        # Handle sales employee auto-selection based on current user
        if self.request and self.request.user.is_authenticated:
            # If user is not a superuser and has a linked sales employee, set it as default
            if not self.request.user.is_superuser:
                try:
                    from ..models import SalesEmployee
                    sales_employee = SalesEmployee.objects.get(user=self.request.user, is_active=True)
                    self.fields['sales_employee'].initial = sales_employee
                    self.fields['sales_employee'].widget.attrs['readonly'] = True
                except:
                    pass

    def clean(self):
        cleaned_data = super().clean()
        sales_order_number = cleaned_data.get('sales_order_number')
        delivery_number = cleaned_data.get('delivery_number')
        
        # Validate sales_order_number if provided
        if sales_order_number:
            try:
                sales_order = SalesOrder.objects.get(id=sales_order_number)
                # Store the actual object for save method
                cleaned_data['sales_order'] = sales_order
            except SalesOrder.DoesNotExist:
                self.add_error('sales_order_number', f"Sales Order #{sales_order_number} does not exist")
        
        # Validate delivery_number if provided
        if delivery_number:
            try:
                delivery = Delivery.objects.get(id=delivery_number)
                # Store the actual object for save method
                cleaned_data['delivery'] = delivery
            except Delivery.DoesNotExist:
                self.add_error('delivery_number', f"Delivery #{delivery_number} does not exist")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the sales_order and delivery from the cleaned data
        if 'sales_order' in self.cleaned_data:
            instance.sales_order = self.cleaned_data['sales_order']
        
        if 'delivery' in self.cleaned_data:
            instance.delivery = self.cleaned_data['delivery']
        
        if commit:
            instance.save()
        
        return instance

class ARInvoiceExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for AR Invoice"""
    discount_amount = forms.DecimalField(required=False, label="Discount Amount")
    tax_amount = forms.DecimalField(required=False, label="Tax Amount")
    total_amount = forms.DecimalField(required=False, label="Total Amount")
    payable_amount = forms.DecimalField(required=False, label="Payable Amount")
    paid_amount = forms.DecimalField(required=False, label="Paid Amount")
    due_amount = forms.DecimalField(required=False, label="Due Amount")    
    class Meta:
        model = ARInvoice
        fields = [
            'contact_person', 'billing_address', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'total_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method', 'payment_reference', 
            'payment_date', 'remarks'
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
            'tax_amount': forms.NumberInput(attrs={
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
        
        # Set initial values of 0 for financial fields if they're empty
        financial_fields = ['discount_amount', 'tax_amount', 'total_amount', 
                           'payable_amount', 'paid_amount', 'due_amount']
        for field in financial_fields:
            if not self.instance.pk or not getattr(self.instance, field):
                self.initial[field] = 0
        
        # Make some fields read-only as they are calculated
        read_only_fields = ['total_amount', 'payable_amount', 'due_amount']
        for field in read_only_fields:
            if field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
            
        # Filter contact persons and addresses by customer if customer is selected
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=customer_id
                )
                self.fields['billing_address'].queryset = Address.objects.filter(
                    business_partner_id=customer_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.customer:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.customer
            )
            self.fields['billing_address'].queryset = Address.objects.filter(
                business_partner=self.instance.customer
            )
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
            self.fields['billing_address'].queryset = Address.objects.none()

    def clean(self):
        cleaned_data = super().clean()
    
        # Handle missing financial fields by providing default values
        financial_fields = ['discount_amount', 'tax_amount', 'total_amount', 
                           'payable_amount', 'paid_amount', 'due_amount']
    
        for field in financial_fields:
            if field not in cleaned_data:
                cleaned_data[field] = 0
    
        # Get values with defaults if not provided
        total_amount = cleaned_data.get('total_amount', 0) or 0
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
    
        # Calculate payable amount
        payable_amount = total_amount
class ARInvoiceLineForm(forms.ModelForm):
    """Form for AR Invoice Line items"""

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
        model = ARInvoiceLine
        fields = [
            'item_code', 'item_name', 'quantity', 'unit_price', 
            'total_amount', 'uom', 'remarks', 'is_active'
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
            'total_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'step': '0.01',
                'min': '0',
                'readonly': 'readonly'
            }),
            'uom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Unit of measure',
                'readonly': 'readonly'
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
        
        # Make total_amount read-only
        if 'total_amount' in self.fields:
            self.fields['total_amount'].widget.attrs['readonly'] = True
        
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
                
        # Calculate total amount
        quantity = cleaned_data.get('quantity', 0) or 0
        unit_price = cleaned_data.get('unit_price', 0) or 0
        
        # Calculate total and quantize to 6 decimal places to match model definition
        total_amount = Decimal(quantity * unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        cleaned_data['total_amount'] = total_amount

        return cleaned_data

# Create formset for ARInvoiceLine
ARInvoiceLineFormSet = inlineformset_factory(
    ARInvoice,
    ARInvoiceLine,
    form=ARInvoiceLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

# Add a wrapper function to pass request to the formset
def get_arinvoice_line_formset(request=None, **kwargs):
    """
    Returns a formset with the request passed to each form
    """
    FormSet = ARInvoiceLineFormSet
    
    if request:
        class RequestFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet(**kwargs)
    
    return FormSet(**kwargs)

class ARInvoiceFilterForm(BaseFilterForm):
    """
    Filter form for AR Invoice.
    """
    MODEL_STATUS_CHOICES = ARInvoice.STATUS_CHOICES

# Helper function to calculate invoice totals
def calculate_invoice_totals(invoice):
    """
    Calculate and update the total amount and due amount for an invoice
    """
    if not invoice:
        return
    
    # Calculate total amount from invoice lines
    total_amount = Decimal('0.00')
    for line in invoice.lines.filter(is_active=True):
        total_amount += line.total_amount
    
    # Round to 2 decimal places for financial values
    invoice.total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Calculate due amount
    invoice.due_amount = invoice.total_amount - (invoice.paid_amount or Decimal('0.00'))
    
    # Save the invoice
    invoice.save(update_fields=['total_amount', 'due_amount'])

# Helper function to copy data from sales order to invoice
def copy_from_sales_order(invoice, sales_order):
    """
    Copy data from sales order to invoice
    """
    if not invoice or not sales_order:
        return
    
    # Copy header information
    invoice.customer = sales_order.customer
    invoice.contact_person = sales_order.contact_person
    invoice.billing_address = sales_order.billing_address
    invoice.currency = sales_order.currency
    invoice.payment_terms = sales_order.payment_terms
    invoice.sales_employee = sales_order.sales_employee
    
    # Copy line items
    for order_line in sales_order.lines.filter(is_active=True):
        invoice_line = ARInvoiceLine(
            invoice=invoice,
            sales_order_line=order_line,
            item_code=order_line.item_code,
            item_name=order_line.item_name,
            quantity=order_line.quantity,
            unit_price=order_line.unit_price,
            uom=order_line.uom,
            remarks=order_line.remarks
        )
        invoice_line.total_amount = Decimal(invoice_line.quantity * invoice_line.unit_price).quantize(Decimal('0.000001'))
        invoice_line.save()
    
    # Calculate totals
    calculate_invoice_totals(invoice)

# Helper function to copy data from delivery to invoice
def copy_from_delivery(invoice, delivery):
    """
    Copy data from delivery to invoice
    """
    if not invoice or not delivery:
        return
    
    # Copy header information
    invoice.customer = delivery.customer
    invoice.contact_person = delivery.contact_person
    invoice.billing_address = delivery.shipping_address  # Use shipping address as billing address
    invoice.currency = delivery.currency
    invoice.payment_terms = delivery.payment_terms
    invoice.sales_employee = delivery.sales_employee
    
    # Copy line items
    for delivery_line in delivery.lines.filter(is_active=True):
        invoice_line = ARInvoiceLine(
            invoice=invoice,
            delivery_line=delivery_line,
            sales_order_line=delivery_line.sales_order_line,
            item_code=delivery_line.item_code,
            item_name=delivery_line.item_name,
            quantity=delivery_line.quantity,
            unit_price=delivery_line.unit_price,
            uom=delivery_line.uom,
            remarks=delivery_line.remarks
        )
        invoice_line.total_amount = Decimal(invoice_line.quantity * invoice_line.unit_price).quantize(Decimal('0.000001'))
        invoice_line.save()
    
    # Calculate totals
    calculate_invoice_totals(invoice)
