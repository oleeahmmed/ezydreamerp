from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from ..models import JournalEntry, JournalEntryLine, ChartOfAccounts, CostCenter
from config.forms import BaseFilterForm

class JournalEntryForm(forms.ModelForm):
    """Form for creating and updating Journal Entry records"""
    
    class Meta:
        model = JournalEntry
        fields = [
            'doc_num', 'posting_date', 'reference', 
            'is_posted', 'currency', 'cost_center'
        ]
        widgets = {
            'doc_num': forms.TextInput(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'placeholder': 'Auto-generated if left blank'
            }),
            'posting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'placeholder': 'Reference'
            }),
            'is_posted': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-[hsl(var(--primary))]'
            }),
            'currency': forms.Select(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            today = timezone.now().date()
            self.initial['posting_date'] = today

class JournalEntryExtraInfoForm(forms.ModelForm):
    """Form for managing financial information and remarks for Journal Entry"""
    
    class Meta:
        model = JournalEntry
        fields = [
            'total_debit', 'total_credit', 'remarks'
        ]
        widgets = {
            'remarks': forms.Textarea(attrs={
                'rows': 4,
                'class': 'peer w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Remarks',
            }),
            'total_debit': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            }),
            'total_credit': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'value': '0.00',
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
            }),
        }

class JournalEntryLineForm(forms.ModelForm):
    """Form for Journal Entry Line items"""
    
    class Meta:
        model = JournalEntryLine
        fields = [
            'account', 'debit_amount', 'credit_amount', 'description'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'placeholder': 'Select account'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'step': '0.01',
                'min': '0'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.TextInput(attrs={
                'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]',
                'placeholder': 'Description'
            }),

        }

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        debit_amount = cleaned_data.get('debit_amount') or 0
        credit_amount = cleaned_data.get('credit_amount') or 0
        
        # Removed the validation that prevents both debit and credit amounts
        # Now users can enter both debit and credit amounts
        
        if debit_amount == 0 and credit_amount == 0:
            self.add_error('debit_amount', 'Either debit or credit amount must be greater than zero')

        return cleaned_data

# Create formset for JournalEntryLine
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class JournalEntryFilterForm(BaseFilterForm):
    """Filter form for Journal Entries"""
    MODEL_STATUS_CHOICES = [
        ('posted', 'Posted'),
        ('draft', 'Draft'),
    ]
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All')] + MODEL_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'premium-input w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))]'
        })
    )