from django import forms

class BaseFilterForm(forms.Form):
    """
    A reusable base filter form to be extended for filtering different models.
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search...',
            'class': 'form-control'
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="From Date"
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="To Date"
    )

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'MODEL_STATUS_CHOICES'):
            self.fields['status'].choices += self.MODEL_STATUS_CHOICES

class CustomTextarea(forms.Textarea):
    """Custom Textarea widget that sets input_type to 'textarea'"""
    input_type = 'textarea'

    def __init__(self, attrs=None):
        default_attrs = {'rows': 4, 'cols': 40}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)