from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from ..models import GoodsIssue, GoodsIssueLine, Item, Warehouse
from .base_forms import CustomTextarea, BaseFilterForm, BaseExtraInfoForm

class GoodsIssueForm(forms.ModelForm):
    """Form for creating and updating Goods Issue records"""
    
    class Meta:
        model = GoodsIssue
        fields = [
            'posting_date', 'status', 
        ]  # Removed document_number
        widgets = {
            'posting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['posting_date'] = today
            self.initial['status'] = 'Posted'

class GoodsIssueExtraInfoForm(forms.ModelForm):
    """Form for managing financial information for Goods Issue"""
    
    class Meta:
        model = GoodsIssue
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
        
        if not self.instance.pk or not self.instance.total_amount:
            self.initial['total_amount'] = 0
            
        if not self.instance.pk or not self.instance.discount_amount:
            self.initial['discount_amount'] = 0
            
        if not self.instance.pk or not self.instance.paid_amount:
            self.initial['paid_amount'] = 0
            
        if 'payable_amount' in self.fields:
            self.fields['payable_amount'].widget.attrs['readonly'] = True
        
        if 'due_amount' in self.fields:
            self.fields['due_amount'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        
        financial_fields = [
            'total_amount', 'discount_amount',
            'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date'
        ]
        
        for field in financial_fields:
            if field not in cleaned_data:
                cleaned_data[field] = 0 if field.endswith('_amount') else None
        
        total_amount = cleaned_data.get('total_amount', 0) or 0
        discount_amount = cleaned_data.get('discount_amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
        
        payable_amount = total_amount - discount_amount
        cleaned_data['payable_amount'] = payable_amount
        
        due_amount = payable_amount - paid_amount
        cleaned_data['due_amount'] = due_amount
        
        if paid_amount > 0 and 'payment_method' in cleaned_data and 'payment_date' in cleaned_data:
            payment_method = cleaned_data.get('payment_method')
            payment_date = cleaned_data.get('payment_date')
            
            if not payment_method and 'payment_method' in self.fields:
                self.add_error('payment_method', 'Payment method is required when paid amount is greater than zero')
            
            if not payment_date and 'payment_date' in self.fields:
                cleaned_data['payment_date'] = timezone.now().date()
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if not hasattr(instance, 'discount_amount') or instance.discount_amount is None:
            instance.discount_amount = 0
            
        if not hasattr(instance, 'total_amount') or instance.total_amount is None:
            instance.total_amount = 0
            
        if not hasattr(instance, 'paid_amount') or instance.paid_amount is None:
            instance.paid_amount = 0
        
        instance.payable_amount = instance.total_amount - instance.discount_amount
        instance.due_amount = instance.payable_amount - instance.paid_amount
        
        if instance.paid_amount > 0 and not instance.payment_date:
            instance.payment_date = timezone.now().date()
            
        if commit:
            instance.save()
        return instance

class GoodsIssueLineForm(forms.ModelForm):
    """Form for Goods Issue Line items"""

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
        model = GoodsIssueLine
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

# Create formset for GoodsIssueLine
GoodsIssueLineFormSet = inlineformset_factory(
    GoodsIssue,
    GoodsIssueLine,
    form=GoodsIssueLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class GoodsIssueFilterForm(BaseFilterForm):
    """
    Filter form for Goods Issue.
    """
    MODEL_STATUS_CHOICES = GoodsIssue.STATUS_CHOICES

