from django import forms
from django.utils import timezone

from ..models import SalesEmployee
from config.forms import BaseFilterForm


class SalesEmployeeForm(forms.ModelForm):
    """Form for creating and updating Sales Employee records"""
    
    class Meta:
        model = SalesEmployee
        fields = [
            'user',  'name', 
            'position', 'department', 'phone', 
            'email', 'notes', 'is_active'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'peer w-full px-3 py-3 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] placeholder-transparent',
                'placeholder': 'Notes',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # If creating a new employee and current user doesn't have an employee record
        if not self.instance.pk and self.request and self.request.user.is_authenticated:
            try:
                # Check if current user already has a sales employee record
                SalesEmployee.objects.get(user=self.request.user)
            except SalesEmployee.DoesNotExist:
                # Set initial values based on the current user
                self.fields['user'].initial = self.request.user
                if not self.initial.get('name') and self.request.user.get_full_name():
                    self.initial['name'] = self.request.user.get_full_name()
                if not self.initial.get('email') and self.request.user.email:
                    self.initial['email'] = self.request.user.email


class SalesEmployeeFilterForm(BaseFilterForm):
    """
    Filter form for Sales Employee.
    """
    MODEL_STATUS_CHOICES = [
        ('', 'All Status'),
        ('True', 'Active'),
        ('False', 'Inactive'),
    ]
    
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Department',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    
    position = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Position',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )