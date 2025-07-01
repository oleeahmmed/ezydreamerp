from django import forms
from django.forms import inlineformset_factory
from ..models import Roster, RosterAssignment, RosterDay, WorkPlace, Shift, Employee
from config.forms import CustomTextarea, BaseFilterForm

class WorkPlaceForm(forms.ModelForm):
    """Form for creating and updating WorkPlace records"""
    
    class Meta:
        model = WorkPlace
        fields = ['name', 'address', 'description']
        widgets = {
            'address': CustomTextarea(),
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

class ShiftForm(forms.ModelForm):
    """Form for creating and updating Shift records"""
    
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'break_time', 'grace_time']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.TimeInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

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

class RosterFilterForm(BaseFilterForm):
    """Form for filtering Roster records"""
    
    MODEL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('upcoming', 'Upcoming'),
    ]

