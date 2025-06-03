from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from decimal import Decimal

from ..models import GoodsReturn, GoodsReturnLine, GoodsReceiptPo, GoodsReceiptPoLine
from Inventory.models import Item, Warehouse
from BusinessPartnerMasterData.models import BusinessPartner, ContactPerson, Address
from config.forms import BaseFilterForm

class GoodsReturnForm(forms.ModelForm):
    """Form for creating and updating Goods Return records"""
    
    class Meta:
        model = GoodsReturn
        fields = [
            'document_date', 'posting_date', 'vendor', 
            'goods_receipt', 'warehouse', 'status', 
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for date fields
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['posting_date'] = today
            self.initial['status'] = 'Draft'
            
        # Filter goods receipts by vendor if vendor is selected
        if 'vendor' in self.data:
            try:
                vendor_id = int(self.data.get('vendor'))
                self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.filter(
                    vendor_id=vendor_id,
                    status__in=['Received', 'Partially Received']
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.vendor:
            self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.filter(
                vendor=self.instance.vendor,
                status__in=['Received', 'Partially Received']
            )
        else:
            self.fields['goods_receipt'].queryset = GoodsReceiptPo.objects.none()

class GoodsReturnExtraInfoForm(forms.ModelForm):
    """Form for managing additional information for Goods Return"""
    
    class Meta:
        model = GoodsReturn
        fields = [
            'contact_person', 'return_address', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'total_amount',
            'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date',
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
            
        # Filter contact persons by vendor if vendor is selected
        if 'vendor' in self.data:
            try:
                vendor_id = int(self.data.get('vendor'))
                self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                    business_partner_id=vendor_id
                )
                self.fields['return_address'].queryset = Address.objects.filter(
                    business_partner_id=vendor_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.vendor:
            self.fields['contact_person'].queryset = ContactPerson.objects.filter(
                business_partner=self.instance.vendor
            )
            self.fields['return_address'].queryset = Address.objects.filter(
                business_partner=self.instance.vendor
            )
        else:
            self.fields['contact_person'].queryset = ContactPerson.objects.none()
            self.fields['return_address'].queryset = Address.objects.none()

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

class GoodsReturnLineForm(forms.ModelForm):
    """Form for Goods Return Line items"""

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
        model = GoodsReturnLine
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
                'step': '0.000001',
                'min': '0.000001'
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

# Create formset for GoodsReturnLine
GoodsReturnLineFormSet = inlineformset_factory(
    GoodsReturn,
    GoodsReturnLine,
    form=GoodsReturnLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class GoodsReturnFilterForm(BaseFilterForm):
    """
    Filter form for Goods Return.
    """
    MODEL_STATUS_CHOICES = GoodsReturn.STATUS_CHOICES