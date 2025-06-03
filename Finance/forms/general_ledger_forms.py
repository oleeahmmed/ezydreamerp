from django import forms
from ..models import GeneralLedger, ChartOfAccounts, JournalEntry, CostCenter, Currency
from config.forms import BaseFilterForm

class GeneralLedgerForm(forms.ModelForm):
    """Form for creating and updating General Ledger records"""
    
    class Meta:
        model = GeneralLedger
        fields = [
            'account', 'posting_date', 'journal_entry', 'debit_amount', 
            'credit_amount', 'balance', 'currency', 'cost_center'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-control',
            }),
            'posting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'journal_entry': forms.Select(attrs={
                'class': 'form-control'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class GeneralLedgerFilterForm(BaseFilterForm):
    """Filter form for General Ledger"""
    
    account = forms.ModelChoiceField(
        queryset=ChartOfAccounts.objects.all(),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    journal_entry = forms.ModelChoiceField(
        queryset=JournalEntry.objects.all(),
        required=False,
        empty_label="All Journal Entries",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

