from django import forms
from ..models import UnitOfMeasure
from .base_forms import CustomTextarea, BaseFilterForm

class UnitOfMeasureForm(forms.ModelForm):
    """Form for creating and updating UnitOfMeasure records"""
    
    code = forms.CharField(
        max_length=20,
        help_text="Unique code for the unit of measure (e.g., PCS, KG, M)",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter unit code (e.g., PCS, KG)'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        help_text="Full name of the unit of measure",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter unit name (e.g., Pieces, Kilograms)'
        })
    )
    
    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'name', ]
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-[hsl(var(--ring))]'
            }),
        }

    def clean_code(self):
        """Convert code to uppercase"""
        code = self.cleaned_data['code'].upper()
        return code

class UnitOfMeasureFilterForm(BaseFilterForm):
    """Form for filtering UnitOfMeasure records"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search units...',
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive'),
        ],
    )
    
    def clean_is_active(self):
        """Convert is_active string to boolean"""
        is_active = self.cleaned_data.get('is_active')
        if is_active == '':
            return None
        return is_active == 'true'