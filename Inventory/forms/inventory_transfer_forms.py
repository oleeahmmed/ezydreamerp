from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from ..models import InventoryTransfer, InventoryTransferLine, Warehouse, Item
from .base_forms import CustomTextarea, BaseFilterForm, BaseExtraInfoForm

class InventoryTransferForm(forms.ModelForm):
    """Form for creating and updating Inventory Transfer records"""
    
    class Meta:
        model = InventoryTransfer
        fields = [
            # 'document_date', 'posting_date', 
            'from_warehouse', 'to_warehouse', 'status'
        ]  # Removed document_number
        widgets = {
            # 'document_date': forms.DateInput(attrs={
            #     'type': 'date',
            #     'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            # }),
            # 'posting_date': forms.DateInput(attrs={
            #     'type': 'date',
            #     'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            # }),
            'from_warehouse': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'to_warehouse': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'reference_document': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Reference Document'
            }),
            'remarks': CustomTextarea(attrs={
                'rows': 3,
                'placeholder': 'Additional notes or comments'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['document_date'] = today
            self.initial['posting_date'] = today
            self.initial['status'] = 'Posted'

class InventoryTransferExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for Inventory Transfer"""
    
    class Meta:
        model = InventoryTransfer
        fields = [
            'total_amount', 'discount_amount',
            'payable_amount', 'remarks'
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk or not self.instance.total_amount:
            self.initial['total_amount'] = 0
            
        if not self.instance.pk or not self.instance.discount_amount:
            self.initial['discount_amount'] = 0
            
        if 'payable_amount' in self.fields:
            self.fields['payable_amount'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        
        total_amount = cleaned_data.get('total_amount', 0) or 0
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        
        payable_amount = total_amount - discount_amount
        cleaned_data['payable_amount'] = payable_amount
        
        return cleaned_data

class InventoryTransferLineForm(forms.ModelForm):
    """Form for Inventory Transfer Line items"""

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
        model = InventoryTransferLine
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

# Create formset for InventoryTransferLine
InventoryTransferLineFormSet = inlineformset_factory(
    InventoryTransfer,
    InventoryTransferLine,
    form=InventoryTransferLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class InventoryTransferFilterForm(BaseFilterForm):
    """
    Filter form for Inventory Transfer.
    """
    MODEL_STATUS_CHOICES = InventoryTransfer.STATUS_CHOICES
