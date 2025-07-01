from django import forms
from django.forms import inlineformset_factory
from ..models import Roster, RosterAssignment, Employee, Shift
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

class RosterAssignmentForm(forms.ModelForm):
    """Form for RosterAssignment inline formset"""
    
    class Meta:
        model = RosterAssignment
        fields = ['employee', 'shift']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        
        # Add labels
        self.fields['employee'].label = "Employee"
        self.fields['shift'].label = "Shift"

# Create formset for RosterAssignment
RosterAssignmentFormSet = inlineformset_factory(
    Roster,
    RosterAssignment,
    form=RosterAssignmentForm,
    extra=1,  # Show 5 empty forms initially
    can_delete=True,
    min_num=1,  # At least one employee required
    validate_min=True
)

class RosterFilterForm(BaseFilterForm):
    """Form for filtering Roster records"""
    
    MODEL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('upcoming', 'Upcoming'),
    ]
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )