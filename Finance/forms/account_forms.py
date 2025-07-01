from django import forms
from ..models import ChartOfAccounts, AccountType
from config.forms import BaseFilterForm

class AccountForm(forms.ModelForm):
    """Form for creating and updating Chart of Accounts records"""
    
    class Meta:
        model = ChartOfAccounts
        fields = ['code', 'name', 'account_type', 'parent', 'is_active', 'currency']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account name'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent accounts to exclude self (for editing)
        if self.instance.pk:
            self.fields['parent'].queryset = ChartOfAccounts.objects.exclude(pk=self.instance.pk)

class AccountFilterForm(BaseFilterForm):
    """Filter form for Chart of Accounts"""
    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        required=False,
        empty_label="All Account Types",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

