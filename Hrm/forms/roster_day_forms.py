from django import forms
from ..models import RosterDay, RosterAssignment, Shift
from config.forms import BaseFilterForm

class RosterDayForm(forms.ModelForm):
    """Form for creating and updating RosterDay records"""
    
    class Meta:
        model = RosterDay
        fields = ['roster_assignment', 'date', 'shift']
        widgets = {
            'roster_assignment': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shift': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text and labels
        self.fields['roster_assignment'].label = "Roster Assignment"
        self.fields['date'].label = "Date"
        self.fields['shift'].label = "Shift"
        
        # Add queryset optimization
        self.fields['roster_assignment'].queryset = RosterAssignment.objects.select_related(
            'employee', 'roster'
        ).all()
        self.fields['shift'].queryset = Shift.objects.all()
        
        # Ensure consistent styling
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.setdefault('class', 'form-control')

class RosterDayFilterForm(BaseFilterForm):
    """Form for filtering RosterDay records"""
    
    roster_assignment = forms.ModelChoiceField(
        queryset=RosterAssignment.objects.select_related('employee', 'roster').all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Roster Assignment",
        empty_label="All Assignments"
    )
    
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Shift",
        empty_label="All Shifts"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date From"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date To"
    )
    
    employee_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by employee name...'
        }),
        label="Employee Search"
    )
