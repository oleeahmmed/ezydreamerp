from django import forms
from django.forms import inlineformset_factory
from ..models import RosterAssignment, RosterDay, Employee, Roster
from config.forms import BaseFilterForm

class RosterAssignmentForm(forms.ModelForm):
    """Form for creating and updating Roster Assignment records"""
    
    class Meta:
        model = RosterAssignment
        fields = ['roster', 'employee']
    
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

class RosterDayForm(forms.ModelForm):
    """Form for creating and updating Roster Day records"""
    
    class Meta:
        model = RosterDay
        fields = ['roster_assignment', 'date', 'shift', 'workplace']
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

