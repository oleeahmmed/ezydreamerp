from django import forms
from ..models import EmployeeSeparation, Employee
from config.forms import CustomTextarea, BaseFilterForm

class EmployeeSeparationForm(forms.ModelForm):
    """Form for creating and updating Employee Separation records"""
    
    class Meta:
        model = EmployeeSeparation
        fields = [
            'employee', 'separation_type', 'separation_date', 'notice_period_served',
            'reason', 'exit_interview_conducted', 'clearance_completed',
            'final_settlement_completed', 'remarks'
        ]
        widgets = {
            'separation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class EmployeeSeparationFilterForm(BaseFilterForm):
    """Form for filtering Employee Separation records"""
    
    MODEL_STATUS_CHOICES = [
        ('RES', 'Resignation'),
        ('TER', 'Termination'),
        ('DIS', 'Dismissal'),
        ('RET', 'Retirement'),
        ('EXP', 'Contract Expiry'),
        ('OTH', 'Other'),
    ]
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    separation_type = forms.ChoiceField(
        choices=[('', 'All Types')] + MODEL_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    clearance_completed = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Yes'), ('false', 'No')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    final_settlement_completed = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Yes'), ('false', 'No')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

