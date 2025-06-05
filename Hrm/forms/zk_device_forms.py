# hrm/forms/zk_device_forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import ZKDevice, Department, Designation, Employee
from config.forms import BaseFilterForm

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
            raise forms.ValidationError(_("IP address is required"))
        return ip_address

class ZKDeviceConnectionTestForm(forms.Form):
    """Form for testing connection to multiple ZK devices"""
    devices = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_("Select Devices"),
        required=True
    )

class ZKDeviceSyncForm(forms.Form):
    """Form for syncing attendance data from ZK Devices"""
    devices = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'custom-checkbox'}),
        required=True,
        label=_("Select Devices")
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'custom-checkbox'}),
        required=False,
        label=_("Select Employees (Optional)")
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

    def clean(self):
        cleaned_data = super().clean()
        devices = cleaned_data.get('devices')
        if not devices:
            raise forms.ValidationError(_("Please select at least one device to sync."))
        return cleaned_data

class EmployeeAttendanceForm(forms.Form):
    """Form for selecting date range to sync employee attendance."""
    start_date = forms.DateField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_("Leave blank to include all past records.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_("Leave blank to include up to today.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be later than end date."))
        return cleaned_data

class ZKUserSyncToEmployeeForm(forms.Form):
    """Form for syncing user data from ZK Devices to Employee model."""
    devices = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Select Devices to Sync Users From")
    )
    default_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        label=_("Default Department for New Employees"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    default_designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        required=True,
        label=_("Default Designation for New Employees"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ZKDeviceFilterForm(BaseFilterForm):
    """Filter form for ZKDevice list view"""
    is_active = forms.ChoiceField(
        required=False,
        label=_('Active Status'),
        choices=[('', _('All')), ('True', _('Active')), ('False', _('Inactive'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_is_active(self):
        value = self.cleaned_data.get('is_active')
        if value == 'True':
            return True
        elif value == 'False':
            return False
        return None

class ZKUserFilterForm(BaseFilterForm):
    """Form for filtering ZK users by device and searching by user ID or name."""
    device = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.all(),
        required=False,
        label=_("Select Devices"),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            'id': 'device-select',
            'data-placeholder': _('Select one or more devices...'),
        })
    )
    search = forms.CharField(
        required=False,
        label=_("Search User"),
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': _('Search by User ID or Name...'),
            'id': 'user-search',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        devices = cleaned_data.get('device')
        search = cleaned_data.get('search', '').strip()

        if not devices and not search:
            raise forms.ValidationError(_("Please select at least one device or enter a search query."))
        
        return cleaned_data

class ZKUserForm(forms.Form):
    """Form for adding and updating ZK users, supporting single device selection."""
    devices = forms.ModelChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
        label=_("Select Device"),
        required=True,
        help_text=_("Select the device to associate with this user.")
    )
    uid = forms.CharField(
        max_length=10,
        label=_("User ID (on Device)"),
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )
    name = forms.CharField(
        max_length=50,
        label=_("Name"),
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )
    privilege = forms.ChoiceField(
        choices=[
            (0, _("Normal User")),
            (1, _("Assignee")),
            (2, _("Manager")),
            (3, _("Admin")),
        ],
        label=_("Role"),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
    )
    card = forms.CharField(
        max_length=20,
        label=_("Card Number"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
        help_text=_("Card number (optional)"),
    )
    password = forms.CharField(
        max_length=20,
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        }),
        help_text=_("Password (optional, numeric only for some devices)"),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'})

        if self.instance:
            try:
                device = getattr(self.instance, 'devices', None) or getattr(self.instance, 'device', None)
                if device and hasattr(device, 'id'):
                    self.fields['devices'].queryset = ZKDevice.objects.filter(id=device.id)
                    self.fields['devices'].initial = device.id
                elif hasattr(self.instance, 'device_id'):
                    self.fields['devices'].queryset = ZKDevice.objects.filter(id=self.instance.device_id)
                    self.fields['devices'].initial = self.instance.device_id
                else:
                    self.fields['devices'].queryset = ZKDevice.objects.none()
                    self.fields['devices'].initial = None
            except Exception as e:
                self.fields['devices'].queryset = ZKDevice.objects.none()
                self.fields['devices'].initial = None
        else:
            self.fields['devices'].queryset = ZKDevice.objects.filter(is_active=True)

class ZKDeviceUserDeleteForm(forms.Form):
    """Form for confirming deletion of a ZK user from a device."""
    confirm = forms.BooleanField(label=_("Confirm Deletion"), required=True,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))