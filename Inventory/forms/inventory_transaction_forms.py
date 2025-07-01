from django import forms
from django.utils import timezone
from ..models import InventoryTransaction, Warehouse
from .base_forms import CustomTextarea

class InventoryTransactionForm(forms.ModelForm):
    """Form for creating and updating Inventory Transaction records"""



    transaction_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
        }),
        help_text="Date and time of the transaction"
    )

    item_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 item-code-autocomplete',
            'placeholder': 'Enter item code'
        }),
        help_text="Code of the item"
    )

    item_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
            'placeholder': 'Item name'
        }),
        help_text="Name of the item"
    )

    quantity = forms.DecimalField(
        max_digits=18,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
            'step': '0.000001'
        }),
        help_text="Quantity"
    )

    unit_price = forms.DecimalField(
        max_digits=18,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
            'step': '0.000001'
        }),
        help_text="Unit price of the item"
    )

    reference = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
            'placeholder': 'Reference number (optional)'
        }),
        help_text="Reference to invoice, PO, or document"
    )

    notes = forms.CharField(
        required=False,
        widget=CustomTextarea(attrs={
            'rows': 4,
            'placeholder': 'Additional notes or comments about this transaction'
        }),
        help_text="Additional notes or comments"
    )

    class Meta:
        model = InventoryTransaction
        fields = [
             'transaction_date', 
            'item_code', 'item_name', 'warehouse', 'quantity', 
            'unit_price', 'reference', 'transaction_type', 'notes'
        ]

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get('quantity', 0)
        unit_price = cleaned_data.get('unit_price', 0)
        cleaned_data['total_amount'] = quantity * unit_price

        return cleaned_data



class InventoryTransactionFilterForm(forms.Form):
    """Form for filtering inventory transactions"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by item code, name, or reference...',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-gray-300 bg-white text-gray-900 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
        })
    )

    warehouse = forms.ModelChoiceField(
        required=False,
        queryset=Warehouse.objects.filter(is_active=True), 
        empty_label="All Warehouses"
    )

    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + InventoryTransaction.TRANSACTION_TYPES,
    )

    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
