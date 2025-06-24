from django import forms
from django.forms import inlineformset_factory
from ..models import RosterAssignment, RosterDay, Employee, Roster, Shift
from config.forms import BaseFilterForm

class RosterAssignmentForm(forms.ModelForm):
    """Form for creating and updating Roster Assignment records"""
    
    class Meta:
        model = RosterAssignment
        fields = ['roster', 'employee', 'shift']
    
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
        
        # Add labels for better UX
        self.fields['roster'].label = "Roster"
        self.fields['employee'].label = "Employee"
        self.fields['shift'].label = "Default Shift"
        
        # Add help text
        self.fields['shift'].help_text = "Default shift for this roster assignment"

class RosterDayForm(forms.ModelForm):
    """Form for creating and updating Roster Day records"""
    
    class Meta:
        model = RosterDay
        fields = ['roster_assignment', 'date', 'shift']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Ensure shift field has proper queryset and initial value
        self.fields['shift'].queryset = Shift.objects.all()
        self.fields['shift'].empty_label = "Select Shift"
        
        # If this is an existing instance, ensure the shift value is properly set
        if self.instance and self.instance.pk and self.instance.shift:
            self.fields['shift'].initial = self.instance.shift.pk

# Create formset for RosterDay
RosterDayFormSet = inlineformset_factory(
    RosterAssignment,
    RosterDay,
    form=RosterDayForm,
    extra=1,
    can_delete=True
)

class RosterAssignmentFilterForm(BaseFilterForm):
    """Form for filtering Roster Assignment records"""
    
    roster = forms.ModelChoiceField(
        queryset=Roster.objects.all(),
        required=False,
        empty_label="All Rosters",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.all(),
        required=False,
        empty_label="All Shifts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
