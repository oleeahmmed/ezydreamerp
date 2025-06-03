from django import forms
from ..models import Department
from config.forms import CustomTextarea, BaseFilterForm

class DepartmentForm(forms.ModelForm):
    """Form for creating and updating Department records"""
    
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
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

class DepartmentFilterForm(BaseFilterForm):
    """Form for filtering Department records"""
    
    code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department Code'})
    )

