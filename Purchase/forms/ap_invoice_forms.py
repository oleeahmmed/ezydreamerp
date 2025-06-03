from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction, models

from ..models import APInvoice, APInvoiceLine, PurchaseOrder, GoodsReceiptPo, PurchaseOrderLine, GoodsReceiptPoLine
from Inventory.models import Item
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class APInvoiceForm(forms.ModelForm):
    """Form for creating and updating AP Invoice records"""
    
    class Meta:
        model = APInvoice
        fields = [
            'document_date', 'posting_date', 'due_date', 'vendor', 
            'purchase_order', 'goods_receipt', 'status', 
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
        super().__init__(*args, **kwargs)
        
        # Set initial values for date fields
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['posting_date'] = today
            self.initial['status'] = 'Open'
            
        # Filter purchase orders and goods receipts by vendor if vendor is selected
        if 'vendor' in self.data:
            try:
                vendor_id = int(self.data.get('vendor'))
                self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                    vendor_id=vendor_id,
                    status__in=['Open', 'Partially Invoiced', 'Received', 'Partially Received']
                )
                self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.filter(
                    vendor_id=vendor_id,
                    status__in=['Received', 'Partially Received']
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.vendor:
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                vendor=self.instance.vendor,
                status__in=['Open', 'Partially Invoiced', 'Received', 'Partially Received']
            )
            self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.filter(
                vendor=self.instance.vendor,
                status__in=['Received', 'Partially Received']
            )
        else:
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.none()
            self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.none()

class APInvoiceExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for AP Invoice"""
    
    class Meta:
        model = APInvoice
        fields = [
            'contact_person', 'billing_address', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'total_amount',
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
            
        # Filter contact persons and addresses by vendor if vendor is selected
        if 'vendor' in self.data:
            try:
                vendor_id = int(self.data.get('vendor'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=vendor_id
                )
                self.fields['billing_address'].queryset = Address.objects.filter(
                    business_partner_id=vendor_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.vendor:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.vendor
            )
            self.fields['billing_address'].queryset = Address.objects.filter(
                business_partner=self.instance.vendor
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
        payable_amount = total_amount - discount_amount
        cleaned_data['payable_amount'] = payable_amount
    
        # Calculate due amount
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
    
        return cleaned_data

class APInvoiceLineForm(forms.ModelForm):
    """Form for AP Invoice Line items"""

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
        model = APInvoiceLine
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
                'step': '0.000001',
                'min': '0.000001'
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
        super().__init__(*args, **kwargs)
        
        # Make total_amount read-only
        if 'total_amount' in self.fields:
            self.fields['total_amount'].widget.attrs['readonly'] = True

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
                if not cleaned_data.get('uom') and item.purchase_uom:
                    cleaned_data['uom'] = item.purchase_uom.code
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist")
                
        # Calculate total amount
        quantity = cleaned_data.get('quantity', 0) or 0
        unit_price = cleaned_data.get('unit_price', 0) or 0
        
        # Calculate total and quantize to 6 decimal places to match model definition
        total_amount = Decimal(quantity * unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        cleaned_data['total_amount'] = total_amount

        return cleaned_data

# Create formset for APInvoiceLine
APInvoiceLineFormSet = inlineformset_factory(
    APInvoice,
    APInvoiceLine,
    form=APInvoiceLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class APInvoiceFilterForm(BaseFilterForm):
    """
    Filter form for AP Invoice.
    """
    MODEL_STATUS_CHOICES = APInvoice.STATUS_CHOICES

# Helper function to copy data from purchase order to invoice
def copy_from_purchase_order(invoice, order):
    """Copy data from purchase order to AP invoice"""
    with transaction.atomic():
        # Copy header data
        invoice.contact_person = order.contact_person
        invoice.billing_address = order.billing_address
        invoice.currency = order.currency
        invoice.payment_terms = order.payment_terms
        invoice.discount_amount = order.discount_amount
        invoice.tax_amount = order.tax_amount
        invoice.remarks = order.remarks
        
        # Calculate due date if payment terms exist
        if invoice.payment_terms:
            from django.utils import timezone
            import datetime
            invoice.due_date = invoice.document_date + datetime.timedelta(days=invoice.payment_terms.days)
        
        # Copy line items
        total_amount = 0
        for order_line in order.lines.filter(is_active=True):
            # Check if line has already been invoiced
            already_invoiced_qty = APInvoiceLine.objects.filter(
                purchase_order_line=order_line,
                invoice__status__in=['Open', 'Partially Paid', 'Paid']
            ).exclude(invoice=invoice).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            remaining_qty = order_line.quantity - already_invoiced_qty
            
            if remaining_qty > 0:
                invoice_line = APInvoiceLine.objects.create(
                    invoice=invoice,
                    purchase_order_line=order_line,
                    item_code=order_line.item_code,
                    item_name=order_line.item_name,
                    quantity=remaining_qty,
                    unit_price=order_line.unit_price,
                    total_amount=Decimal(remaining_qty * order_line.unit_price).quantize(Decimal('0.000001')),
                    uom=order_line.uom,
                    remarks=order_line.remarks,
                    is_active=True
                )
                total_amount += invoice_line.total_amount
        
        # Update invoice totals
        invoice.total_amount = total_amount
        invoice.payable_amount = total_amount - invoice.discount_amount
        invoice.due_amount = invoice.payable_amount - invoice.paid_amount
        invoice.save()

# Helper function to copy data from goods receipt to invoice
def copy_from_goods_receipt(invoice, goods_receipt):
    """Copy data from goods receipt to AP invoice"""
    with transaction.atomic():
        # Copy header data
        invoice.contact_person = goods_receipt.contact_person
        if goods_receipt.purchase_order:
            invoice.billing_address = goods_receipt.purchase_order.billing_address
        invoice.currency = goods_receipt.currency
        invoice.payment_terms = goods_receipt.payment_terms
        invoice.discount_amount = goods_receipt.discount_amount
        invoice.tax_amount = goods_receipt.tax_amount
        invoice.remarks = goods_receipt.remarks
        
        # Calculate due date if payment terms exist
        if invoice.payment_terms:
            from django.utils import timezone
            import datetime
            invoice.due_date = invoice.document_date + datetime.timedelta(days=invoice.payment_terms.days)
        
        # Copy line items
        total_amount = 0
        for receipt_line in goods_receipt.lines.filter(is_active=True):
            # Check if line has already been invoiced
            already_invoiced_qty = APInvoiceLine.objects.filter(
                goods_receipt_line=receipt_line,
                invoice__status__in=['Open', 'Partially Paid', 'Paid']
            ).exclude(invoice=invoice).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            remaining_qty = receipt_line.quantity - already_invoiced_qty
            
            if remaining_qty > 0:
                invoice_line = APInvoiceLine.objects.create(
                    invoice=invoice,
                    goods_receipt_line=receipt_line,
                    purchase_order_line=receipt_line.purchase_order_line,
                    item_code=receipt_line.item_code,
                    item_name=receipt_line.item_name,
                    quantity=remaining_qty,
                    unit_price=receipt_line.unit_price,
                    total_amount=Decimal(remaining_qty * receipt_line.unit_price).quantize(Decimal('0.000001')),
                    uom=receipt_line.uom,
                    remarks=receipt_line.remarks,
                    is_active=True
                )
                total_amount += invoice_line.total_amount
        
        # Update invoice totals
        invoice.total_amount = total_amount
        invoice.payable_amount = total_amount - invoice.discount_amount
        invoice.due_amount = invoice.payable_amount - invoice.paid_amount
        invoice.save()

# Helper function to calculate invoice totals
def calculate_invoice_totals(invoice):
    """
    Calculate invoice totals based on line items
    """
    if not invoice:
        return
    
    # Calculate total amount from line items
    total_amount = sum(line.total_amount for line in invoice.lines.filter(is_active=True))
    invoice.total_amount = total_amount
    
    # Calculate payable amount
    invoice.payable_amount = invoice.total_amount - invoice.discount_amount
    
    # Calculate due amount
    invoice.due_amount = invoice.payable_amount - invoice.paid_amount
    
    invoice.save()