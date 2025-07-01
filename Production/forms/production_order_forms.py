from django import forms
from django.forms import inlineformset_factory
from ..models import ProductionOrder, ProductionOrderComponent, Item, BillOfMaterials, Warehouse

class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['order_number', 'document_date', 'product', 'bom', 'warehouse', 'planned_quantity', 'status', 'remarks']
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-input'}),
            'document_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bom': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Item.objects.filter(is_active=True)
        self.fields['bom'].queryset = BillOfMaterials.objects.filter(status='Active')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        self.fields['order_number'].required = False  # Auto-generated
        self.fields['document_date'].required = True
        self.fields['product'].required = True
        self.fields['bom'].required = True
        self.fields['warehouse'].required = True
        self.fields['planned_quantity'].required = True
        self.fields['status'].required = True

class ProductionOrderComponentForm(forms.ModelForm):
    class Meta:
        model = ProductionOrderComponent
        fields = ['item_code', 'item_name', 'planned_quantity']
        widgets = {
            'item_code': forms.TextInput(attrs={'class': 'form-input'}),
            'item_name': forms.TextInput(attrs={'class': 'form-input'}),
            'planned_quantity': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item_code'].required = False  # Allow empty rows initially
        self.fields['item_name'].required = False  # Allow empty rows initially
        self.fields['planned_quantity'].required = False  # Allow empty rows initially

ProductionOrderComponentFormSet = inlineformset_factory(
    ProductionOrder,
    ProductionOrderComponent,
    form=ProductionOrderComponentForm,
    extra=1,  # Start with 1 empty row
    can_delete=True,
    min_num=0,
    validate_min=False  # Don't require minimum forms
)

class ProductionOrderFilterForm(forms.Form):
    order_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Filter by order number'})
    )
    product = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by product'})
    )
    bom = forms.ModelChoiceField(
        queryset=BillOfMaterials.objects.filter(status='Active'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by BOM'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by warehouse'})
    )
    status = forms.ChoiceField(
        choices=ProductionOrder.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by status'})
    )
