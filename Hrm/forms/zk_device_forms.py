from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import ZKDevice

class ZKDeviceForm(forms.ModelForm):
    """Form for creating and updating ZK devices"""

    class Meta:
        model = ZKDevice
        fields = [
            'name', 'ip_address', 'port', 'device_id', 'is_active',
            'timeout', 'password', 'force_udp'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'device_id': forms.TextInput(attrs={'class': 'form-control'}),
            'timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'force_udp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap or Tailwind classes uniformly
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean_port(self):
        value = self.cleaned_data.get("port")
        return int(value) if value not in [None, ''] else 4370

    def clean_timeout(self):
        value = self.cleaned_data.get("timeout")
        return int(value) if value not in [None, ''] else 5

    def clean_ip_address(self):
        ip_address = self.cleaned_data.get('ip_address')
        if not ip_address:
            raise forms.ValidationError("IP address is required")
        return ip_address

class ZKDeviceConnectionTestForm(forms.Form):
    """Form for testing connection to a ZK device"""
    device = forms.ModelChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ZKDeviceSyncForm(forms.Form):
    """Form for syncing data from ZK devices"""
    devices = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Select Devices")
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_("Start Date (Optional)")
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_("End Date (Optional)")
    )


class ZKDeviceFilterForm(forms.Form):
    """Filter form for ZKDevice list view"""
    search = forms.CharField(
        required=False,
        label='Search by name or IP',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'})
    )
    is_active = forms.ChoiceField(
        required=False,
        label='Active Status',
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_is_active(self):
        value = self.cleaned_data.get('is_active')
        if value == 'True':
            return True
        elif value == 'False':
            return False
        return None