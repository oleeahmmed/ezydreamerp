from django import forms
from ..models import ShortLeaveApplication, Employee
from config.forms import CustomTextarea, BaseFilterForm

class ShortLeaveApplicationForm(forms.ModelForm):
    """Form for creating and updating Short Leave Application records"""
    
    class Meta:
        model = ShortLeaveApplication
        fields = [
            'employee', 'date', 'start_time', 'end_time', 
            'reason', 'status', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': CustomTextarea(),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class ShortLeaveApplicationFilterForm(BaseFilterForm):
    """Form for filtering Short Leave Application records"""
    
    MODEL_STATUS_CHOICES = [
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('CAN', 'Cancelled'),
    ]
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

