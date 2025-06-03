from django import forms
from ..models import CostCenter
from config.forms import BaseFilterForm

class CostCenterForm(forms.ModelForm):
    """Form for creating and updating Cost Center records"""
    
    class Meta:
        model = CostCenter
        fields = ['code', 'name', 'parent', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter name'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select parent cost center (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class CostCenterFilterForm(BaseFilterForm):
    """Filter form for Cost Centers"""
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('true', 'Active'), ('false', 'Inactive')],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )