from django import forms
from ..models import Warehouse
from .base_forms import CustomTextarea, BaseFilterForm

class WarehouseForm(forms.ModelForm):
    """Form for creating and updating Warehouse records"""
    
    code = forms.CharField(
        max_length=8,
        help_text="Unique warehouse code (max 8 characters)",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter warehouse code'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        help_text="Warehouse name",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter warehouse name'
        })
    )
    

    
    class Meta:
        model = Warehouse
        fields = [
            'code', 'name',
        ]
        widgets = {
            'is_default': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-[hsl(var(--ring))]'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-[hsl(var(--ring))]'
            }),
        }
        help_texts = {
            'is_default': 'Set as the default warehouse',
            'is_active': 'Whether this warehouse is active',
        }

    def clean_code(self):
        """Convert code to uppercase"""
        code = self.cleaned_data['code'].upper()
        return code

class WarehouseFilterForm(BaseFilterForm):
    """Form for filtering Warehouse records"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search warehouses...',
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive')
        ],
    )
    
    is_default = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Warehouses'),
            ('true', 'Default Only'),
            ('false', 'Non-Default Only')
        ],
    )
    
    def clean_is_active(self):
        """Convert is_active string to boolean"""
        is_active = self.cleaned_data.get('is_active')
        if is_active == '':
            return None
        return is_active == 'true'
        
    def clean_is_default(self):
        """Convert is_default string to boolean"""
        is_default = self.cleaned_data.get('is_default')
        if is_default == '':
            return None
        return is_default == 'true'