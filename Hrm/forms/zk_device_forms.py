# hrm/forms/zk_device_forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import ZKDevice, Department, Designation, Employee,ZKAttendanceLog
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

class EmployeeAttendanceReportForm(forms.Form):
    """Form for selecting date range to generate attendance report."""
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

class ZKAttendanceLogForm(forms.ModelForm):
    """Form for creating and updating ZK Attendance Logs."""
    
    # Punch Type Choices (based on ZKTeco standards)
    PUNCH_TYPE_CHOICES = [
        ('', _('Select Punch Type')),
        ('Check In', _('Check In')),
        ('Check Out', _('Check Out')),
        ('Break Out', _('Break Out')),
        ('Break In', _('Break In')),
        ('Overtime In', _('Overtime In')),
        ('Overtime Out', _('Overtime Out')),
        ('Unknown', _('Unknown')),
    ]
    
    # Status Choices (ZKTeco device status codes)
    STATUS_CHOICES = [
        ('', _('Select Status')),
        (0, _('Normal')),
        (1, _('Absent')),
        (2, _('Late')),
        (3, _('Early Leave')),
        (4, _('Overtime')),
        (5, _('Holiday')),
        (6, _('Weekend')),
        (7, _('Invalid')),
    ]
    
    # Verification Type Choices (ZKTeco verification methods)
    VERIFY_TYPE_CHOICES = [
        ('', _('Select Verification Type')),
        (0, _('Password')),
        (1, _('Fingerprint')),
        (2, _('Card')),
        (3, _('Password + Fingerprint')),
        (4, _('Password + Card')),
        (5, _('Fingerprint + Card')),
        (6, _('Password + Fingerprint + Card')),
        (7, _('Face')),
        (8, _('Face + Fingerprint')),
        (9, _('Face + Password')),
        (10, _('Face + Card')),
        (15, _('Palm')),
        (16, _('Palm + Fingerprint')),
        (17, _('Palm + Password')),
        (18, _('Palm + Card')),
    ]
    
    # Work Code Choices (common work codes)
    WORK_CODE_CHOICES = [
        ('', _('Select Work Code')),
        (0, _('Normal Work')),
        (1, _('Overtime')),
        (2, _('Holiday Work')),
        (3, _('Weekend Work')),
        (4, _('Night Shift')),
        (5, _('Special Duty')),
        (6, _('Training')),
        (7, _('Meeting')),
        (8, _('Business Trip')),
        (9, _('Other')),
    ]
    
    class Meta:
        model = ZKAttendanceLog
        fields = ['device', 'user_id', 'timestamp', 'punch_type', 'status', 'verify_type', 'work_code']
        widgets = {
            'device': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': _('Select Device')
            }),
            'user_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter User ID'),
                'pattern': '[0-9]+',
                'title': _('Please enter a valid user ID (numbers only)')
            }),
            'timestamp': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'punch_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'verify_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'work_code': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'device': _('Device'),
            'user_id': _('User ID'),
            'timestamp': _('Timestamp'),
            'punch_type': _('Punch Type'),
            'status': _('Status'),
            'verify_type': _('Verification Method'),
            'work_code': _('Work Code'),
        }
        help_texts = {
            'device': _('Select the ZKTeco device that recorded this attendance'),
            'user_id': _('Enter the employee/user ID from the device'),
            'timestamp': _('Date and time when the attendance was recorded'),
            'punch_type': _('Type of attendance action (Check In, Check Out, etc.)'),
            'status': _('Attendance status code'),
            'verify_type': _('Method used for verification (Fingerprint, Card, etc.)'),
            'work_code': _('Work classification code'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for select fields
        self.fields['punch_type'] = forms.ChoiceField(
            choices=self.PUNCH_TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        self.fields['status'] = forms.ChoiceField(
            choices=self.STATUS_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        self.fields['verify_type'] = forms.ChoiceField(
            choices=self.VERIFY_TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        self.fields['work_code'] = forms.ChoiceField(
            choices=self.WORK_CODE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        # Limit device choices to active devices only
        self.fields['device'].queryset = ZKDevice.objects.filter(is_active=True).order_by('name')
        
        # Set required fields
        self.fields['device'].required = True
        self.fields['user_id'].required = True
        self.fields['timestamp'].required = True
        
        # Optional fields
        self.fields['punch_type'].required = False
        self.fields['status'].required = False
        self.fields['verify_type'].required = False
        self.fields['work_code'].required = False
        
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            
            # Add validation classes
            if field.required:
                field.widget.attrs['class'] += ' required'

    def clean_user_id(self):
        """Validate user_id field."""
        user_id = self.cleaned_data.get('user_id')
        if user_id:
            # Remove any whitespace
            user_id = user_id.strip()
            # Validate that it's not empty after stripping
            if not user_id:
                raise forms.ValidationError(_('User ID cannot be empty.'))
        return user_id

    def clean_timestamp(self):
        """Validate timestamp field."""
        timestamp = self.cleaned_data.get('timestamp')
        if timestamp:
            from django.utils import timezone
            import datetime
            
            # Check if timestamp is not in the future (with 5 minute tolerance)
            now = timezone.now()
            future_limit = now + datetime.timedelta(minutes=5)
            
            if timestamp > future_limit:
                raise forms.ValidationError(_('Timestamp cannot be more than 5 minutes in the future.'))
                
            # Check if timestamp is not too old (more than 1 year)
            past_limit = now - datetime.timedelta(days=365)
            if timestamp < past_limit:
                raise forms.ValidationError(_('Timestamp cannot be more than 1 year in the past.'))
                
        return timestamp

    def clean(self):
        """Perform cross-field validation."""
        cleaned_data = super().clean()
        device = cleaned_data.get('device')
        user_id = cleaned_data.get('user_id')
        timestamp = cleaned_data.get('timestamp')
        
        # Check for duplicate records (same device, user, timestamp, punch_type)
        if device and user_id and timestamp:
            punch_type = cleaned_data.get('punch_type')
            
            # Build the query
            duplicate_query = ZKAttendanceLog.objects.filter(
                device=device,
                user_id=user_id,
                timestamp=timestamp
            )
            
            # If punch_type is provided, include it in the duplicate check
            if punch_type:
                duplicate_query = duplicate_query.filter(punch_type=punch_type)
            
            # Exclude current instance if updating
            if self.instance and self.instance.pk:
                duplicate_query = duplicate_query.exclude(pk=self.instance.pk)
            
            if duplicate_query.exists():
                raise forms.ValidationError(
                    _('An attendance record with the same device, user ID, timestamp, and punch type already exists.')
                )
        
        return cleaned_data

class ZKAttendanceLogFilterForm(forms.Form):
    """Form for filtering ZK Attendance Logs."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by User ID or Device...'),
            'autocomplete': 'off'
        }),
        label=_('Search')
    )
    
    device = forms.ModelChoiceField(
        queryset=ZKDevice.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label=_('All Devices'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label=_('Device')
    )
    
    user_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('User ID'),
            'pattern': '[0-9]*',
            'autocomplete': 'off'
        }),
        label=_('User ID')
    )
    
    punch_type = forms.ChoiceField(
        choices=[('', _('All Punch Types'))] + ZKAttendanceLogForm.PUNCH_TYPE_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Punch Type')
    )
    
    verify_type = forms.ChoiceField(
        choices=[('', _('All Verification Types'))] + ZKAttendanceLogForm.VERIFY_TYPE_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Verification Type')
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Start Date')
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('End Date')
    )
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_('Start date cannot be later than end date.'))
                
        return cleaned_data