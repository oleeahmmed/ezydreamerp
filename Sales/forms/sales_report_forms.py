from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ..models import SalesEmployee
from BusinessPartnerMasterData.models import BusinessPartner
from config.forms import BaseFilterForm

class SalesReportFilterForm(BaseFilterForm):
    """Filter form for sales reports with specified fields"""
    
    # Customer filter
    customer = forms.ModelChoiceField(
        queryset=BusinessPartner.objects.filter(bp_type='C'),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    # Sales Employee filter
    sales_employee = forms.ModelChoiceField(
        queryset=SalesEmployee.objects.all(),
        required=False,
        empty_label="All Sales Employees",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    # Date filters
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Start Date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'End Date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update field widgets with consistent styling
        self.fields['search'].widget.attrs.update({
            'placeholder': 'Search Sales Order ID...',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
        
        # Remove status field (already handled by parent __init__ in BaseFilterForm)
        self.fields.pop('status', None)