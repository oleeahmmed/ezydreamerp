from django import forms
from ..models import WorkPlace
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

class WorkPlaceFilterForm(BaseFilterForm):
    """Form for filtering WorkPlace records"""
    
    # No additional fields needed beyond the base search field

