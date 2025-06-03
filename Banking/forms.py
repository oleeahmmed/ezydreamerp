from django import forms
from django.db import models
from decimal import Decimal
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Payment, PaymentLine, PaymentMethod
from config.forms import BaseFilterForm, CustomTextarea
from global_settings.models import Currency
from BusinessPartnerMasterData.models import BusinessPartner
from Finance.models import ChartOfAccounts 
class PaymentMethodForm(forms.ModelForm):
    """Form for creating and updating Payment Method records"""
    
    class Meta:
        model = PaymentMethod
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'description': CustomTextarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

class PaymentMethodFilterForm(BaseFilterForm):
    """Filter form for Payment Method"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove date fields as they're not relevant for payment methods
        self.fields.pop('date_from', None)
        self.fields.pop('date_to', None)
        self.fields.pop('status', None)
        
        # Customize search placeholder
        self.fields['search'].widget.attrs['placeholder'] = 'Search by name...'

class PaymentForm(forms.ModelForm):
    """Form for creating and updating Payment records"""
    
    class Meta:
        model = Payment
        fields = ['doc_num',  'payment_type', 'payment_date', 'payment_method', 'currency','amount','sales_order']
        widgets = {
            'doc_num': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'type': 'text'  # Correctly specify the input type here
            }),
            # 'business_partner': forms.Select(attrs={
            #     'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            # }),
            'payment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'sales_order': forms.Select(attrs={'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'}),  

        }
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sales_order'].required = True

        # Set default values for the fields if not already provided
        if not self.instance.pk:  # This ensures defaults are set only on new instances, not on updates
            self.fields['doc_num'].initial = self.generate_doc_num()  # Set default doc_num
            self.fields['payment_type'].initial = 'incoming'  # Default to 'incoming'
            self.fields['payment_method'].initial = PaymentMethod.objects.first()  # Default to the first record
            self.fields['currency'].initial = Currency.objects.first()  # Default to the first record
            self.initial['payment_date'] = timezone.now().date()

    def generate_doc_num(self):
        """
        A custom method to generate doc_num. 
        This method ensures that we always increment from the last doc_num.
        """
        last_payment = Payment.objects.order_by('-id').first()  # Get the most recent Payment object

        if last_payment:
            try:
                last_num = int(last_payment.doc_num.split('-')[1])  # Extract the number after the dash
                return f"PAY-{last_num + 1}"  # Increment the last number by 1
            except (IndexError, ValueError):  # Handle cases where doc_num format is not as expected
                return f"PAY-1"  # If the format is incorrect, start with PAY-1
        else:
            return f"PAY-1"  # If no payments exist, start with PAY-1

    def clean(self):
        cleaned_data = super().clean()
        
        # Set the business_partner from sales_order if it's not already set
        sales_order = cleaned_data.get('sales_order')
        if not cleaned_data.get('business_partner') and sales_order:
            cleaned_data['business_partner'] = sales_order.customer  # Automatically set business partner from sales order
        
        amount = cleaned_data.get('amount')

        # Ensure the payment doesn't exceed the sales order total amount
        if sales_order and amount:
            total_paid = Payment.objects.filter(sales_order=sales_order).aggregate(
                total_paid=models.Sum('amount')
            )['total_paid'] or Decimal(0)

            if total_paid + amount > sales_order.total_amount:
                self.add_error('amount', _('The payment amount exceeds the total amount of the sales order.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set business_partner from sales_order if available
        if instance.sales_order:
            instance.business_partner = instance.sales_order.customer
        
        if commit:
            instance.save()
        return instance    
class PaymentExtraInfoForm(forms.ModelForm):
    """Form for managing additional information for Payment"""
    
    class Meta:
        model = Payment
        fields = [
            'amount', 'reference', 'remarks', 
            'is_reconciled', 
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'remarks': CustomTextarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'is_reconciled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
            }),

        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values of 0 for financial fields if they're empty
        if not self.instance.pk or not self.instance.amount:
            self.initial['amount'] = 0
            

            

    
    def clean(self):
        cleaned_data = super().clean()
        
        # Calculate due amount
        amount = cleaned_data.get('amount', 0) or 0
        paid_amount = cleaned_data.get('paid_amount', 0) or 0
        due_amount = amount - paid_amount
        cleaned_data['due_amount'] = due_amount
        
        return cleaned_data

class PaymentLineForm(forms.ModelForm):
    """Form for Payment Line items"""

    class Meta:
        model = PaymentLine
        fields = ['account', 'amount', 'description']
        widgets = {
            'account': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = ChartOfAccounts.objects.all()

# Create formset for PaymentLine
PaymentLineFormSet = inlineformset_factory(
    Payment,
    PaymentLine,
    form=PaymentLineForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=True
)

class PaymentFilterForm(BaseFilterForm):
    """Filter form for Payment"""
    
    PAYMENT_TYPE_CHOICES = [
        ('', 'All Types'),
        ('incoming', 'Incoming Payment'),
        ('outgoing', 'Outgoing Payment'),
    ]
    
    payment_type = forms.ChoiceField(
        required=False,
        choices=PAYMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        }),
    )
    
    is_reconciled = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Reconciliation Status'),
            ('true', 'Reconciled'),
            ('false', 'Not Reconciled'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        }),
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize search placeholder
        self.fields['search'].widget.attrs['placeholder'] = 'Search by document number or reference...'

