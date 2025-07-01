from django import forms
from ..models import LeaveBalance, Employee, LeaveType
from config.forms import BaseFilterForm, CustomTextarea

class LeaveBalanceForm(forms.ModelForm):
    """Form for creating and updating Leave Balance records"""
    
    class Meta:
        model = LeaveBalance
        fields = [
            'employee', 'leave_type', 'year', 'total_days', 
            'used_days', 'pending_days', 'carried_forward_days'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        
        # Add help text
        self.fields['total_days'].help_text = "Total allocated days for this leave type"
        self.fields['used_days'].help_text = "Days already used by the employee"
        self.fields['pending_days'].help_text = "Days in pending leave applications"
        self.fields['carried_forward_days'].help_text = "Days carried forward from previous year"

class LeaveBalanceFilterForm(BaseFilterForm):
    """Form for filtering Leave Balance records"""
    
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
    
    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate year choices (current year and 5 years back)
        import datetime
        current_year = datetime.datetime.now().year
        year_choices = [(str(year), str(year)) for year in range(current_year-5, current_year+2)]
        self.fields['year'].choices = [('', 'All Years')] + year_choices

class LeaveBalanceInitializeForm(forms.Form):
    """Form for initializing leave balances for all employees"""

    year = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    leave_types = forms.ModelMultipleChoiceField(
        queryset=LeaveType.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    reset_existing = forms.BooleanField(
        required=False,
        initial=False,
        help_text="If checked, existing leave balances will be reset to default values",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import datetime
        current_year = datetime.datetime.now().year
        year_choices = [(str(year), str(year)) for year in range(current_year, current_year + 2)]
        self.fields['year'].choices = year_choices
        self.fields['year'].initial = str(current_year)

    def clean_leave_types(self):
        """Custom clean method to filter out invalid values like 'on'"""
        raw_ids = self.data.getlist('leave_types')
        valid_ids = [pk for pk in raw_ids if pk.isdigit()]
        leave_types = LeaveType.objects.filter(id__in=valid_ids)

        if not leave_types.exists():
            raise forms.ValidationError("Please select at least one valid leave type.")

        return leave_types
