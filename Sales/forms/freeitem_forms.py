from django import forms
from Inventory.models import Item
from Sales.models import FreeItemDiscount


class FreeItemDiscountForm(forms.ModelForm):
    class Meta:
        model = FreeItemDiscount
        fields = ['item', 'buy_quantity', 'free_quantity', 'free_item']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-control'
            }),
            'buy_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'free_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'free_item': forms.Select(attrs={
                'class': 'form-control'
            }),
        }