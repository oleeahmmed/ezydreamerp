from django import forms
from datetime import datetime, timedelta
from ..models import AttendanceMonth, AttendanceLog, Attendance, OvertimeRecord, Employee
from config.forms import CustomTextarea, BaseFilterForm

class AttendanceMonthForm(forms.ModelForm):
    """Form for creating and updating Attendance Month records"""
    
    class Meta:
        model = AttendanceMonth
        fields = ['year', 'month', 'is_processed']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
        
        # Add month choices
        self.fields['month'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['month'].choices = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]

class AttendanceLogForm(forms.ModelForm):
    """Form for creating and updating Attendance Log records"""
    
    class Meta:
        model = AttendanceLog
        fields = ['employee', 'timestamp', 'is_in', 'location', 'device', 'notes']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.DateTimeInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class AttendanceForm(forms.ModelForm):
    """Form for creating and updating Attendance records"""
    
    class Meta:
        model = Attendance
        fields = [
            'employee', 'date', 'status', 'roster_day', 'check_in', 'check_out',
            'late_minutes', 'early_out_minutes', 'overtime_minutes', 'is_manual', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_in': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'check_out': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class OvertimeRecordForm(forms.ModelForm):
    """Form for creating and updating Overtime Record records"""
    
    class Meta:
        model = OvertimeRecord
        fields = [
            'employee', 'date', 'start_time', 'end_time', 'hours',
            'reason', 'status', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': CustomTextarea(),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.TimeInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        hours = cleaned_data.get('hours')
        
        if start_time and end_time:
            # Calculate hours if not provided
            if not hours:
                start_datetime = datetime.combine(datetime.today(), start_time)
                end_datetime = datetime.combine(datetime.today(), end_time)
                
                # If end time is earlier than start time, it means the overtime spans across midnight
                if end_datetime < start_datetime:
                    end_datetime = end_datetime + timedelta(days=1)
                
                duration = end_datetime - start_datetime
                calculated_hours = duration.total_seconds() / 3600
                cleaned_data['hours'] = round(calculated_hours, 2)
        
        return cleaned_data

class AttendanceFilterForm(BaseFilterForm):
    """Form for filtering Attendance records"""
    
    MODEL_STATUS_CHOICES = [
        ('PRE', 'Present'),
        ('ABS', 'Absent'),
        ('LAT', 'Late'),
        ('LEA', 'Leave'),
        ('HOL', 'Holiday'),
        ('WEE', 'Weekend'),
        ('HAL', 'Half Day'),
    ]
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update employee queryset to only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

