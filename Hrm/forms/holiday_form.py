from django import forms
from ..models import Holiday
from config.forms import CustomTextarea, BaseFilterForm

class HolidayForm(forms.ModelForm):
    """Form for creating and updating Holiday records"""
    
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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

class HolidayFilterForm(BaseFilterForm):
    """Form for filtering Holiday records"""
    
    year = forms.ChoiceField(
        required=False,
        choices=[('', 'All Years')],  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add year choices (current year and 5 years back)
        import datetime
        current_year = datetime.datetime.now().year
        year_choices = [('', 'All Years')]
        for year in range(current_year, current_year - 6, -1):
            year_choices.append((str(year), str(year)))
        self.fields['year'].choices = year_choices

