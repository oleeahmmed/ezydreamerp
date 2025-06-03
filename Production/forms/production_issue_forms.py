from django import forms
from django.forms import inlineformset_factory

from ..models import ProductionIssue, ProductionIssueLine, ProductionOrder, ProductionOrderComponent
from Inventory.models import Warehouse
from config.forms import BaseFilterForm

class ProductionIssueForm(forms.ModelForm):
    """Form for creating and updating Production Issue records"""
    
    class Meta:
        model = ProductionIssue
        fields = [
            'document_date', 'production_order', 'warehouse', 
            'status', 'remarks'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter production order choices to only include active orders
        self.fields['production_order'].queryset = ProductionOrder.objects.filter(
            status__in=['Released', 'In Process']
        )


class ProductionIssueLineForm(forms.ModelForm):
    """Form for Production Issue Line items"""

    class Meta:
        model = ProductionIssueLine
        fields = ['component', 'item_code', 'item_name', 'quantity']
        widgets = {
            'item_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 text-sm border rounded-md bg-[hsl(var(--background))] premium-input text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))] focus:border-[hsl(var(--border))] item-code-input',
                'placeholder': 'Item Code',
                'readonly': 'readonly'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 text-sm border rounded-md bg-[hsl(var(--background))] premium-input text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))] focus:border-[hsl(var(--border))] item-name-input',
                'placeholder': 'Item Name',
                'readonly': 'readonly'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 text-sm border rounded-md bg-[hsl(var(--background))] premium-input text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))] focus:border-[hsl(var(--border))] quantity-input',
                'min': '0.000001',
                'step': '0.000001'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance with a component, populate the item fields
        instance = kwargs.get('instance')
        if instance and instance.component:
            self.initial['item_code'] = instance.component.item_code
            self.initial['item_name'] = instance.component.item_name

# Create formset for ProductionIssueLine
ProductionIssueLineFormSet = inlineformset_factory(
    ProductionIssue,
    ProductionIssueLine,
    form=ProductionIssueLineForm,
    extra=1,
    can_delete=True
)

class ProductionIssueFilterForm(BaseFilterForm):
    """
    Filter form for Production Issue.
    """
    MODEL_STATUS_CHOICES = ProductionIssue.STATUS_CHOICES
    
    production_order = forms.ModelChoiceField(
        queryset=ProductionOrder.objects.all(),
        required=False,
        empty_label="All Production Orders"
    )
    
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True),
        required=False,
        empty_label="All Warehouses"
    )
