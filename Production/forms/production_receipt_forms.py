from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import ProductionReceipt, ProductionReceiptLine, ProductionOrder
from Inventory.models import Warehouse, Item
from config.forms import BaseFilterForm

class ProductionReceiptForm(forms.ModelForm):
    """Form for creating and updating Production Receipt records"""
    
    class Meta:
        model = ProductionReceipt
        fields = [
            'document_date', 'production_order', 'warehouse', 'status'
        ]
        widgets = {
            'document_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'production_order': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if not self.instance.pk:
            self.initial['document_date'] = timezone.now().date()
            self.initial['status'] = 'Draft'
        
        # Restrict production orders to Released or In Process
        self.fields['production_order'].queryset = ProductionOrder.objects.filter(
            status__in=['Released', 'In Process']
        )

        # Restrict warehouses to active ones
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)

class ProductionReceiptExtraInfoForm(forms.ModelForm):
    """Form for managing additional information for Production Receipt"""
    
    class Meta:
        model = ProductionReceipt
        fields = ['remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Enter remarks'
            }),
        }

class ProductionReceiptLineForm(forms.ModelForm):
    """Form for Production Receipt Line items"""

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
        model = ProductionReceiptLine
        fields = ['item_code', 'item_name', 'quantity', 'uom', 'remarks']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Item name',
                'readonly': 'readonly'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'step': '0.000001',
                'min': '0.000001'
            }),
            'uom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Unit of measure',
                'readonly': 'readonly'
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-700',
                'placeholder': 'Remarks'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Make item_name and uom read-only
        self.fields['item_name'].widget.attrs['readonly'] = True
        self.fields['uom'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        item_code = cleaned_data.get('item_code')

        # Validate item selection
        if not item_code:
            self.add_error('item_code', 'Item code is required')
        else:
            try:
                item = Item.objects.get(code=item_code)
                cleaned_data['item_name'] = item.name
                if not cleaned_data.get('uom') and item.sales_uom:
                    cleaned_data['uom'] = item.sales_uom.name
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist")

        return cleaned_data

# Create formset for ProductionReceiptLine
ProductionReceiptLineFormSet = inlineformset_factory(
    ProductionReceipt,
    ProductionReceiptLine,
    form=ProductionReceiptLineForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

# Wrapper function to pass request to formset
def get_production_receipt_line_formset(request=None, **kwargs):
    """
    Returns a formset with the request passed to each form
    """
    FormSet = ProductionReceiptLineFormSet
    
    if request:
        class RequestFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                kwargs['form_kwargs'] = {'request': request}
                super().__init__(*args, **kwargs)
        
        return RequestFormSet(**kwargs)
    
    return FormSet(**kwargs)

class ProductionReceiptFilterForm(BaseFilterForm):
    """
    Filter form for Production Receipt.
    """
    MODEL_STATUS_CHOICES = ProductionReceipt.STATUS_CHOICES