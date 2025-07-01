from django import forms
from ..models import LeaveApplication, Employee, LeaveType
from config.forms import CustomTextarea, BaseFilterForm

class LeaveApplicationForm(forms.ModelForm):
    """Form for creating and updating Leave Application records"""
    
    class Meta:
        model = LeaveApplication
        fields = [
            'employee', 'leave_type', 'start_date', 'end_date', 
            'reason', 'status', 'remarks'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': CustomTextarea(),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        
        # If user is not superuser, set employee to current user and hide status field
        if self.user and not self.user.is_superuser:
            try:
                # Try to get the employee profile for the current user
                employee = Employee.objects.get(user=self.user)
                self.fields['employee'].initial = employee
                self.fields['employee'].widget = forms.HiddenInput()
                
                # Hide status field for non-superusers
                if 'status' in self.fields:
                    self.fields.pop('status')
            except Employee.DoesNotExist:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date cannot be before start date')
        
        # If user is not superuser, force employee to be the current user's employee profile
        if self.user and not self.user.is_superuser:
            try:
                employee = Employee.objects.get(user=self.user)
                cleaned_data['employee'] = employee
            except Employee.DoesNotExist:
                self.add_error('employee', 'You do not have an employee profile')
        
        return cleaned_data

class LeaveApplicationFilterForm(BaseFilterForm):
    """Form for filtering Leave Application records"""
    
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
    
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.all(),
        required=False,
        empty_label="All Leave Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )