from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from ..models import GoodsReceipt, GoodsReceiptLine, Item, Warehouse
from .base_forms import CustomTextarea, BaseFilterForm, BaseExtraInfoForm



class GoodsReceiptForm(forms.ModelForm):
    """Form for creating and updating Goods Receipt records"""

    class Meta:
        model = GoodsReceipt
        fields = ['posting_date', 'status']  
        widgets = {
            'posting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.now().date()
        self.initial['posting_date'] = today
        self.initial['status'] = 'Posted'


class GoodsReceiptExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for Goods Receipt"""
    
    class Meta:
        model = GoodsReceipt  # Add the model here
        fields = [
            'total_amount', 'discount_amount',
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
            'total_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
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
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values of 0 for financial fields if they're empty
        if not self.instance.pk or not self.instance.total_amount:
            self.initial['total_amount'] = 0
            
        if not self.instance.pk or not self.instance.discount_amount:
            self.initial['discount_amount'] = 0
            
        if not self.instance.pk or not self.instance.paid_amount:
            self.initial['paid_amount'] = 0
            
        # Make some fields read-only as they are calculated
        if 'payable_amount' in self.fields:
            self.fields['payable_amount'].widget.attrs['readonly'] = True
        
        if 'due_amount' in self.fields:
            self.fields['due_amount'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Handle missing financial fields by providing default values
        # This allows the form to work even if financial fields are removed from the HTML
        financial_fields = [
            'total_amount', 'tax_amount', 'freight_amount', 'discount_amount',
            'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date'
        ]
        
        for field in financial_fields:
            if field not in cleaned_data:
                cleaned_data[field] = 0 if field.endswith('_amount') else None
        
        # Get values with defaults if not provided
        total_amount = cleaned_data.get('total_amount', 0) or 0
        tax_amount = cleaned_data.get('tax_amount', 0) or 0
        freight_amount = cleaned_data.get('freight_amount', 0) or 0
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
        
        # Calculate payable amount
        payable_amount = total_amount + tax_amount + freight_amount - discount_amount
        cleaned_data['payable_amount'] = payable_amount
        
        # Calculate due amount
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
        
        # Only validate payment fields if paid amount > 0 and the fields exist in the form
        if paid_amount > 0 and 'payment_method' in cleaned_data and 'payment_date' in cleaned_data:
            payment_method = cleaned_data.get('payment_method')
            payment_date = cleaned_data.get('payment_date')
            
            if not payment_method and 'payment_method' in self.fields:
                self.add_error('payment_method', 'Payment method is required when paid amount is greater than zero')
            
            if not payment_date and 'payment_date' in self.fields:
                # Automatically set payment date to today if not provided
                cleaned_data['payment_date'] = timezone.now().date()
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure financial fields have default values if they're missing
        if not hasattr(instance, 'tax_amount') or instance.tax_amount is None:
            instance.tax_amount = 0
            
        if not hasattr(instance, 'freight_amount') or instance.freight_amount is None:
            instance.freight_amount = 0
            
        if not hasattr(instance, 'discount_amount') or instance.discount_amount is None:
            instance.discount_amount = 0
            
        if not hasattr(instance, 'total_amount') or instance.total_amount is None:
            instance.total_amount = 0
            
        if not hasattr(instance, 'paid_amount') or instance.paid_amount is None:
            instance.paid_amount = 0
        
        # Recalculate payable and due amounts
        instance.payable_amount = instance.total_amount + instance.tax_amount + instance.freight_amount - instance.discount_amount
        instance.due_amount = instance.payable_amount - instance.paid_amount
        
        # Set payment date if paid amount > 0 and no payment date
        if instance.paid_amount > 0 and not instance.payment_date:
            instance.payment_date = timezone.now().date()
            
        if commit:
            instance.save()
        return instance



class GoodsReceiptLineForm(forms.ModelForm):
    """Form for Goods Receipt Line items"""

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
        model = GoodsReceiptLine
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

# ✅ Create formset for GoodsReceiptLine
GoodsReceiptLineFormSet = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptLine,
    form=GoodsReceiptLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

from config.forms import BaseFilterForm
class GoodsReceiptFilterForm(BaseFilterForm):
    """
    Filter form for Goods Receipt.
    """
    MODEL_STATUS_CHOICES = GoodsReceipt.STATUS_CHOICES

