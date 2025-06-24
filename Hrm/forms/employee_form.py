from django import forms
from ..models import Employee, Department, Designation
from config.forms import CustomTextarea, BaseFilterForm

class EmployeeForm(forms.ModelForm):
    """Form for creating and updating Employee records"""
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name','name','card_no', 'gender', 'date_of_birth',
            'blood_group',  'default_shift','marital_status', 'email', 'phone', 'emergency_contact_name',
            'emergency_contact_phone', 'present_address', 'permanent_address',
            'department', 'designation', 'joining_date', 'confirmation_date',
            'basic_salary', 'is_active', 'profile_picture','expected_work_hours','overtime_grace_minutes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'confirmation_date': forms.DateInput(attrs={'type': 'date'}),
            'present_address': CustomTextarea(),
            'permanent_address': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })

class EmployeeFilterForm(BaseFilterForm):
    """Form for filtering Employee records"""
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        empty_label="All Designations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'All Status'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

