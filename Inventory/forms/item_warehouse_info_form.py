from django import forms
from django.core.exceptions import ValidationError
from ..models import ItemWarehouseInfo, Item, Warehouse
from .base_forms import CustomTextarea

class ItemWarehouseInfoForm(forms.ModelForm):
    class Meta:
        model = ItemWarehouseInfo
        fields = [
            'item', 'warehouse', 'in_stock', 'committed', 
            'ordered', 'available', 'min_stock', 'max_stock', 'reorder_point','is_active'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'select2'}),
            'warehouse': forms.Select(attrs={'class': 'select2'}),
            'in_stock': forms.NumberInput(attrs={'step': '0.000001'}),
            'committed': forms.NumberInput(attrs={'step': '0.000001'}),
            'ordered': forms.NumberInput(attrs={'step': '0.000001'}),
            'available': forms.NumberInput(attrs={'step': '0.000001', 'readonly': True}),
            'min_stock': forms.NumberInput(attrs={'step': '0.000001'}),
            'max_stock': forms.NumberInput(attrs={'step': '0.000001'}),
        }
        help_texts = {
            'item': 'Select the item',
            'warehouse': 'Select the warehouse',
            'in_stock': 'Current quantity in stock',
            'committed': 'Quantity committed to orders',
            'ordered': 'Quantity on order',
            'available': 'Available quantity (in_stock - committed)',
            'min_stock': 'Minimum stock level for this item in this warehouse',
            'max_stock': 'Maximum stock level for this item in this warehouse',
            'is_active': 'Whether this warehouse-item relationship is active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active records only
        self.fields['item'].queryset = Item.objects.filter(is_active=True)
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        
        # Make available field read-only
        self.fields['available'].widget.attrs['readonly'] = True
        self.fields['available'].required = False
        
        # If this is an existing record, make item and warehouse read-only
        if self.instance.pk:
            self.fields['item'].widget.attrs['readonly'] = True
            self.fields['warehouse'].widget.attrs['readonly'] = True
            self.fields['item'].disabled = True
            self.fields['warehouse'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Calculate available quantity
        in_stock = cleaned_data.get('in_stock') or 0
        committed = cleaned_data.get('committed') or 0
        cleaned_data['available'] = in_stock - committed
        
        # Validate min and max stock
        min_stock = cleaned_data.get('min_stock')
        max_stock = cleaned_data.get('max_stock')
        
        if min_stock is not None and max_stock is not None and min_stock > max_stock:
            raise ValidationError({'min_stock': 'Minimum stock cannot be greater than maximum stock'})
        
        # Validate that item-warehouse combination is unique
        item = cleaned_data.get('item')
        warehouse = cleaned_data.get('warehouse')
        
        if item and warehouse:
            if self.instance.pk:
                # For existing records, we don't need to check uniqueness of the same record
                existing = ItemWarehouseInfo.objects.filter(
                    item=item, 
                    warehouse=warehouse
                ).exclude(pk=self.instance.pk).exists()
            else:
                # For new records, check if the combination already exists
                existing = ItemWarehouseInfo.objects.filter(
                    item=item, 
                    warehouse=warehouse
                ).exists()
                
            if existing:
                raise ValidationError(
                    "An inventory record for this item and warehouse already exists."
                )
                
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Always recalculate available before saving
        instance.available = (instance.in_stock or 0) - (instance.committed or 0)
        
        if commit:
            instance.save()
        
        return instance

class ItemWarehouseInfoFilterForm(forms.Form):
    """Form for filtering item warehouse info in the list view"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search items...',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

    warehouse = forms.ModelChoiceField(
        required=False,
        queryset=Warehouse.objects.filter(is_active=True),
        empty_label="All Warehouses",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

    item_group = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        empty_label="All Item Groups",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

    stock_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Stock Status'),
            ('low', 'Low Stock'),
            ('normal', 'Normal Stock'),
            ('high', 'High Stock'),
            ('out', 'Out of Stock'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

    def __init__(self, *args, **kwargs):
        from ..models import ItemGroup
        super().__init__(*args, **kwargs)
        
        # Set the queryset for item_group
        self.fields['item_group'].queryset = ItemGroup.objects.filter(is_active=True).order_by('name')
        
        # Add help text
        self.fields['search'].help_text = "Search by item code or name"
        self.fields['warehouse'].help_text = "Filter by warehouse"
        self.fields['item_group'].help_text = "Filter by item group"
        self.fields['stock_status'].help_text = "Filter by stock status"
        self.fields['is_active'].help_text = "Filter by status"

    def clean_is_active(self):
        """Clean the is_active field to handle empty values"""
        is_active = self.cleaned_data.get('is_active')
        if is_active == '':
            return None
        return is_active == 'true'
