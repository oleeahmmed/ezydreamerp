from django import forms
from django.forms import inlineformset_factory
from ..models import BillOfMaterials, BOMComponent, BOMType
from Inventory.models import Item, UnitOfMeasure

class BillOfMaterialsForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['code', 'name', 'product', 'bom_type', 'uom', 'x_quantity', 'project', 'status', 'other_cost_percentage', 'additional_cost']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bom_type': forms.Select(attrs={'class': 'form-select'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
            'x_quantity': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'project': forms.TextInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'other_cost_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'additional_cost': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
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

class BOMComponentForm(forms.ModelForm):
    class Meta:
        model = BOMComponent
        fields = ['item_code', 'item_name', 'quantity', 'unit', 'unit_price']
        widgets = {
            'item_code': forms.TextInput(attrs={'class': 'form-input'}),
            'item_name': forms.TextInput(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
            'unit': forms.TextInput(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item_code'].required = True
        self.fields['item_name'].required = True
        self.fields['quantity'].required = True
        self.fields['unit_price'].required = True

BOMComponentFormSet = inlineformset_factory(
    BillOfMaterials, BOMComponent, form=BOMComponentForm,     extra=1,can_delete=True, min_num=0,validate_min=True
)

class BillOfMaterialsFilterForm(forms.Form):
    code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Filter by code'}))
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Filter by name'}))
    product = forms.ModelChoiceField(queryset=Item.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'Filter by product'}))
    bom_type = forms.ChoiceField(choices=BOMType.choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(choices=BillOfMaterials.STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))