from django import forms
from ..models import Roster
from config.forms import CustomTextarea, BaseFilterForm

class RosterForm(forms.ModelForm):
    """Form for creating and updating Roster records"""
    
    class Meta:
        model = Roster
        fields = ['name', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class RosterFilterForm(BaseFilterForm):
    """Form for filtering Roster records"""
    
    MODEL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('upcoming', 'Upcoming'),
    ]

