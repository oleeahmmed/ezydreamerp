from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ..models import SalesEmployee
from BusinessPartnerMasterData.models import BusinessPartner
from Inventory.models import Item

class SalesReportForm(forms.Form):
    """Form for filtering sales reports"""
    
    from_date = forms.DateField(
        label=_("From Date"),
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        }),
        initial=timezone.now().replace(day=1)  # First day of current month
    )
    
    to_date = forms.DateField(
        label=_("To Date"),
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        }),
        initial=timezone.now()  # Current date
    )
    
    business_partner = forms.ModelChoiceField(
        label=_("Customer"),
        queryset=BusinessPartner.objects.filter(bp_type='C', active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    sales_employee = forms.ModelChoiceField(
        label=_("Sales Employee"),
        queryset=SalesEmployee.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    product = forms.ModelChoiceField(
        label=_("Product"),
        queryset=Item.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    report_type = forms.ChoiceField(
        label=_("Report Type"),
        choices=[
            ('detail', _('Detailed Report')),
            ('summary', _('Summary Report')),
        ],
        initial='detail',
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError(_("From date cannot be after to date"))
        
        return cleaned_data