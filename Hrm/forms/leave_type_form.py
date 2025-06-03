from django import forms
from ..models import LeaveType
from config.forms import CustomTextarea, BaseFilterForm

class LeaveTypeForm(forms.ModelForm):
    """Form for creating and updating Leave Type records"""
    
    class Meta:
        model = LeaveType
        fields = [
            'name', 'code', 'description', 'paid', 
            'max_days_per_year', 'carry_forward', 'max_carry_forward_days'
        ]
        widgets = {
            'description': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })

class LeaveTypeFilterForm(BaseFilterForm):
    """Form for filtering Leave Type records"""
    
    paid = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Paid'), ('false', 'Unpaid')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    carry_forward = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Yes'), ('false', 'No')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

