from django import forms
from ..models import Designation, Department
from config.forms import CustomTextarea, BaseFilterForm

class DesignationForm(forms.ModelForm):
    """Form for creating and updating Designation records"""
    
    class Meta:
        model = Designation
        fields = ['name', 'department', 'description']
        widgets = {
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
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class DesignationFilterForm(BaseFilterForm):
    """Form for filtering Designation records"""
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

