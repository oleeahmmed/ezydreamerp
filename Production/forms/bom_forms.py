from django import forms
from django.forms import inlineformset_factory
from ..models import BillOfMaterials, BOMComponent, BOMType
from Inventory.models import Item, UnitOfMeasure

class BillOfMaterialsForm(forms.ModelForm):
    """Form for creating and updating Bill of Materials records"""
    
    class Meta:
        model = BillOfMaterials
        fields = ['code', 'name', 'product', 'bom_type', 'uom', 'x_quantity', 'project', 'status', 'other_cost_percentage', 'additional_cost']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Enter BOM code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Enter BOM name'
            }),
            'product': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'bom_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'choices': [('', ''), ('Standard', 'Standard'), ('Engineering', 'Engineering'), ('Phantom', 'Phantom')]
            }),
            'uom': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'x_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.000001',
                'min': '0'
            }),
            'project': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Enter project name'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'choices': [('', ''), ('Draft', 'Draft'), ('Open', 'Open'), ('Approved', 'Approved'), ('Closed', 'Closed')]
            }),
            'other_cost_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.01',
                'min': '0',
                'value': '0.00'
            }),
            'additional_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.01',
                'min': '0',
                'value': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['product'].queryset = Item.objects.filter(is_active=True)
        self.fields['uom'].queryset = UnitOfMeasure.objects.filter(is_active=True)

        self.fields['code'].required = True
        self.fields['name'].required = True
        self.fields['product'].required = True
        self.fields['bom_type'].required = True
        self.fields['uom'].required = True
        self.fields['x_quantity'].required = True
        self.fields['status'].required = True

        if not self.instance.pk:
            self.initial['status'] = 'Draft'
            self.initial['x_quantity'] = 1.0
            self.initial['other_cost_percentage'] = 0.0
            self.initial['additional_cost'] = 0.0

        if self.request and self.request.user.is_authenticated and not self.request.user.is_superuser:
            self.fields['other_cost_percentage'].widget.attrs['readonly'] = True
            self.fields['additional_cost'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        product = cleaned_data.get('product')
        x_quantity = cleaned_data.get('x_quantity')
        other_cost_percentage = cleaned_data.get('other_cost_percentage', 0) or 0
        additional_cost = cleaned_data.get('additional_cost', 0) or 0

        if code:
            queryset = BillOfMaterials.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error('code', f"BOM with code {code} already exists")

        if product and not product.is_active:
            self.add_error('product', 'Selected product is not active')

        if x_quantity is not None and x_quantity <= 0:
            self.add_error('x_quantity', 'Quantity must be greater than zero')

        if other_cost_percentage < 0:
            self.add_error('other_cost_percentage', 'Other cost percentage cannot be negative')
        if additional_cost < 0:
            self.add_error('additional_cost', 'Additional cost cannot be negative')

        return cleaned_data

class BOMComponentForm(forms.ModelForm):
    """Form for BOM Component items"""

    item_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] item-code-autocomplete',
            'placeholder': 'Enter item code',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = BOMComponent
        fields = ['item_code', 'item_name', 'quantity', 'unit', 'unit_price']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Item name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.000001',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': 'Unit of measure'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.000001',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['item_code'].required = True
        self.fields['item_name'].required = True
        self.fields['quantity'].required = True
        self.fields['unit_price'].required = True

        if self.request and self.request.user.is_authenticated and not self.request.user.is_superuser:
            self.fields['unit_price'].widget.attrs['readonly'] = True

        # Remove default initial values unless instance exists
        if not self.instance.pk:
            self.initial.clear()

    def clean(self):
        cleaned_data = super().clean()
        item_code = cleaned_data.get('item_code')
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')

        if not item_code:
            self.add_error('item_code', 'Item code is required')
        else:
            try:
                item = Item.objects.get(code=item_code, is_active=True)
                if not cleaned_data.get('item_name'):
                    cleaned_data['item_name'] = item.name
                if not cleaned_data.get('unit') and item.sales_uom:
                    cleaned_data['unit'] = item.sales_uom.name
            except Item.DoesNotExist:
                self.add_error('item_code', f"Item with code {item_code} does not exist or is not active")

        if quantity is not None and quantity <= 0:
            self.add_error('quantity', 'Quantity must be greater than zero')

        if unit_price is not None and unit_price < 0:
            self.add_error('unit_price', 'Unit price cannot be negative')

        return cleaned_data

BOMComponentFormSet = inlineformset_factory(
    BillOfMaterials,
    BOMComponent,
    form=BOMComponentForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class BillOfMaterialsFilterForm(forms.Form):
    code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Filter by code'}))
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Filter by name'}))
    product = forms.ModelChoiceField(queryset=Item.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by product'}))
    bom_type = forms.ChoiceField(choices=BOMType.choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(choices=BillOfMaterials.STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))