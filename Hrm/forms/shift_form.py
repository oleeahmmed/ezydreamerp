from django import forms
from ..models import Shift
from config.forms import BaseFilterForm

class ShiftForm(forms.ModelForm):
    """Form for creating and updating Shift records"""
    
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'break_time', 'grace_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'break_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'grace_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure consistent styling (optional, as widgets already include form-control)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.TimeInput)):
                field.widget.attrs.setdefault('class', 'form-control')

class ShiftFilterForm(BaseFilterForm):
    """Form for filtering Shift records"""
    
    start_time_from = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Start Time From"
    )
    
    start_time_to = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Start Time To"
    )