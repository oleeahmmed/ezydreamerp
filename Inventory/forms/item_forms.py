from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
import random
import string
from django.utils import timezone
from decimal import Decimal
from PIL import Image
import os

from ..models import Item, ItemGroup, UnitOfMeasure, Warehouse, ItemWarehouseInfo
from .base_forms import CustomTextarea, BaseFilterForm, BaseExtraInfoForm

class ItemForm(forms.ModelForm):
    """Form for creating and updating Item records"""
    
    code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Auto-generated code',
            'class': 'uppercase w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter item name',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=CustomTextarea(attrs={
            'rows': 3,
            'placeholder': 'Enter item description',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    in_stock = forms.DecimalField(
        required=False,
        disabled=True,
        label="Current Stock",
        widget=forms.NumberInput(attrs={
            'readonly': True,
            'class': 'bg-[hsl(var(--muted))] cursor-not-allowed w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            'step': '0.000001'
        })
    )
    
    class Meta:
        model = Item
        fields = [
            'code', 'name', 'description', 'item_group', 'image', 'is_active',
            'inventory_uom', 'purchase_uom', 'sales_uom',
            'default_warehouse', 'minimum_stock', 'maximum_stock', 'reorder_point',
            'barcode', 'weight', 'volume', 'image_url',
            'is_inventory_item', 'is_sales_item', 'is_purchase_item', 'is_service',
            'unit_price', 'item_cost', 'purchase_price', 'selling_price',
            'markup_percentage', 'discount_percentage'
        ]
        widgets = {
            'item_group': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'inventory_uom': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'purchase_uom': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'sales_uom': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'default_warehouse': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'barcode': forms.TextInput(attrs={
                'placeholder': 'Enter barcode',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'weight': forms.NumberInput(attrs={
                'step': '0.001',
                'placeholder': 'Enter weight',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'volume': forms.NumberInput(attrs={
                'step': '0.001',
                'placeholder': 'Enter volume',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'image_url': forms.URLInput(attrs={
                'placeholder': 'Enter image URL',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'Enter minimum stock',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'maximum_stock': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'Enter maximum stock',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': 'Enter reorder point',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'unit_price': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter unit price',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'item_cost': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter item cost',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter purchase price',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'selling_price': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter selling price',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'markup_percentage': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter markup percentage',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter discount percentage',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[hsl(var(--primary))] focus:ring-[hsl(var(--primary))]'
            }),
            'is_inventory_item': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[hsl(var(--primary))] focus:ring-[hsl(var(--primary))]'
            }),
            'is_sales_item': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[hsl(var(--primary))] focus:ring-[hsl(var(--primary))]'
            }),
            'is_purchase_item': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[hsl(var(--primary))] focus:ring-[hsl(var(--primary))]'
            }),
            'is_service': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-[hsl(var(--primary))] focus:ring-[hsl(var(--primary))]'
            }),
        }

    fieldsets = [
        {
            'title': 'Basic Information',
            'description': 'Enter the required information for the item',
            'icon': 'info',
            'fields': ['code', 'name', 'item_group', 'image', 'inventory_uom', 'default_warehouse', 'is_active', 'item_cost', 'purchase_price','unit_price', 'weight'],
        },
        {
            'title': 'Stock Management',
            'description': 'Configure warehouse and stock settings',
            'icon': 'box',
            'fields': ['minimum_stock', 'maximum_stock', 'reorder_point']
        },
        # {
        #     'title': 'Item Type',
        #     'description': 'Define the type and nature of the item',
        #     'icon': 'tag',
        #     'fields': ['is_inventory_item', 'is_sales_item', 'is_purchase_item', 'is_service']
        # },
        # {
        #     'title': 'Pricing Information',
        #     'description': 'Set pricing details for the item',
        #     'icon': 'dollar-sign',
        #     'fields': ['item_cost', 'purchase_price','unit_price', ]
        # },
        # {
        #     'title': 'Additional Information',
        #     'description': 'Other item details and attributes',
        #     'icon': 'info',
        #     'fields': ['description', 'purchase_uom', 'sales_uom', 'volume', 'image_url']
        # },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purchase_uom'].required = False
        self.fields['sales_uom'].required = False
        self.fields['default_warehouse'].required = False
        
        # Filter active records only
        self.fields['item_group'].queryset = ItemGroup.objects.filter(is_active=True)
        self.fields['inventory_uom'].queryset = UnitOfMeasure.objects.filter(is_active=True)
        self.fields['purchase_uom'].queryset = UnitOfMeasure.objects.filter(is_active=True)
        self.fields['sales_uom'].queryset = UnitOfMeasure.objects.filter(is_active=True)
        self.fields['default_warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        
        # Get all warehouse info if this is an existing item
        self.warehouse_info = []
        if self.instance.pk:
            self.warehouse_info = (
                self.instance.warehouse_info.select_related('warehouse')
                .order_by('-warehouse__is_default', 'warehouse__name')
                .all()
            )
                
        # Auto-select default warehouse if none is specified
        if not self.instance.default_warehouse:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.fields['default_warehouse'].initial = first_warehouse.pk
            else:
                self.fields['default_warehouse'].initial = None
            
        # Handle item code generation and display
        if self.instance.pk:
            # Editing existing item - make code read-only
            self.fields['code'].widget.attrs['readonly'] = True
            self.fields['code'].widget.attrs['class'] += ' readonly'
        else:
            # New item - generate unique code
            self.fields['code'].initial = self._generate_unique_code()
            
        # Set the initial value for the in_stock field
        if self.instance.pk:
            self.fields['in_stock'].initial = self.instance.in_stock
    
    def _generate_unique_code(self):
        """Generate a unique item code"""
        while True:
            # Generate a random 8-character code: 2 letters followed by 6 numbers
            letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            numbers = ''.join(random.choices(string.digits, k=6))
            code = f"{letters}{numbers}"
            
            # Check if this code exists
            if not Item.objects.filter(code=code).exists():
                return code

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate code uniqueness and format
        code = cleaned_data.get('code')
        if code:
            code = code.upper()
            if self.instance.pk:
                # Editing - ensure code hasn't been tampered with
                if code != self.instance.code:
                    raise ValidationError({'code': 'Item code cannot be changed'})
            else:
                # New item - ensure code is unique
                if Item.objects.filter(code=code).exists():
                    raise ValidationError({'code': 'This code is already in use'})
        cleaned_data['code'] = code

        # Validate stock levels
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        reorder_point = cleaned_data.get('reorder_point')

        if minimum_stock and maximum_stock and minimum_stock > maximum_stock:
            raise ValidationError({'minimum_stock': 'Minimum stock cannot be greater than maximum stock'})
        if reorder_point and maximum_stock and reorder_point > maximum_stock:
            raise ValidationError({'reorder_point': 'Reorder point cannot be greater than maximum stock'})
        if minimum_stock and reorder_point and minimum_stock > reorder_point:
            raise ValidationError({'minimum_stock': 'Minimum stock cannot be greater than reorder point'})

        # Set default UOMs if not specified
        if not cleaned_data.get('purchase_uom'):
            cleaned_data['purchase_uom'] = cleaned_data.get('inventory_uom')
        if not cleaned_data.get('sales_uom'):
            cleaned_data['sales_uom'] = cleaned_data.get('inventory_uom')

        return cleaned_data

    def get_stock_display(self):
        """Return formatted stock information for display"""
        if not self.instance.pk:
            return None
            
        return {
            'in_stock': self.instance.in_stock,
            'committed': self.instance.committed,
            'available': self.instance.available,
            'ordered': self.instance.ordered,
        }

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        
        # Update or create warehouse info with current stock
        if instance.is_inventory_item and instance.default_warehouse:
            warehouse_info, created = ItemWarehouseInfo.objects.get_or_create(
                item=instance,
                warehouse=instance.default_warehouse,
                defaults={
                    'in_stock': 0,
                    'committed': 0,
                    'ordered': 0,
                    'available': 0,
                    'min_stock': instance.minimum_stock,
                    'max_stock': instance.maximum_stock
                }
            )
            
            if not created:
                # Update existing warehouse info
                warehouse_info.min_stock = instance.minimum_stock
                warehouse_info.max_stock = instance.maximum_stock
                warehouse_info.save()
                
        # Update the in_stock field after saving
        self.fields['in_stock'].initial = instance.in_stock
        
        return instance

class ItemExtraInfoForm(BaseExtraInfoForm):
    """Form for managing additional information for Item"""
    
    class Meta:
        model = Item
        fields = [
            'description', 'barcode', 'weight', 'volume', 'image_url',
            'is_inventory_item', 'is_sales_item', 'is_purchase_item', 'is_service',
            'markup_percentage', 'discount_percentage'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Description',
            }),
            'barcode': forms.TextInput(attrs={
                'placeholder': 'Enter barcode',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'weight': forms.NumberInput(attrs={
                'step': '0.001',
                'placeholder': 'Enter weight',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'volume': forms.NumberInput(attrs={
                'step': '0.001',
                'placeholder': 'Enter volume',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'image_url': forms.URLInput(attrs={
                'placeholder': 'Enter image URL',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'markup_percentage': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter markup percentage',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'Enter discount percentage',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

class ItemFilterForm(BaseFilterForm):
    """
    Filter form for Item.
    """
    MODEL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    group = forms.ModelChoiceField(
        required=False,
        queryset=ItemGroup.objects.filter(is_active=True),
        empty_label="All Groups",
        widget=forms.Select(attrs={
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

    type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('inventory', 'Inventory Items'),
            ('sales', 'Sales Items'),
            ('purchase', 'Purchase Items'),
            ('service', 'Service Items'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update querysets to only show active records
        self.fields['group'].queryset = ItemGroup.objects.filter(is_active=True).order_by('name')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True).order_by('name')

