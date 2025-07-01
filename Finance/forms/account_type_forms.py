from django import forms
from ..models import AccountType
from config.forms import BaseFilterForm

class AccountTypeForm(forms.ModelForm):
    """Form for creating and updating Account Type records"""
    
    class Meta:
        model = AccountType
        fields = ['code', 'name', 'is_debit']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter name'
            }),
            'is_debit': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class AccountTypeFilterForm(BaseFilterForm):
    """Filter form for Account Types"""
    pass

