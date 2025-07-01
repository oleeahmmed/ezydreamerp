# from django import forms
# from ..models import Employee, Department, Designation
# from config.forms import CustomTextarea, BaseFilterForm

# class EmployeeForm(forms.ModelForm):
#     """Form for creating and updating Employee records"""
    
#     class Meta:
#         model = Employee
#         fields = [
#             'employee_id', 'first_name', 'last_name','name', 'father_name','mother_name','card_no', 'gender', 'date_of_birth',
#             'blood_group',  'default_shift','marital_status', 'email', 'phone', 'emergency_contact_name',
#             'emergency_contact_phone', 'present_address', 'permanent_address',
#             'department', 'designation', 'joining_date', 'confirmation_date',
#             'basic_salary','gross_salary', 'is_active', 'profile_picture','expected_work_hours','overtime_grace_minutes'
#         ]
#         widgets = {
#             'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
#             'joining_date': forms.DateInput(attrs={'type': 'date'}),
#             'confirmation_date': forms.DateInput(attrs={'type': 'date'}),
#             'present_address': CustomTextarea(),
#             'permanent_address': CustomTextarea(),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Apply common styling to all fields
#         for field_name, field in self.fields.items():
#             if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
#                 field.widget.attrs.update({
#                     'class': 'form-control'
#                 })
#             elif isinstance(field.widget, forms.Select):
#                 field.widget.attrs.update({
#                     'class': 'form-control'
#                 })
#             elif isinstance(field.widget, forms.DateInput):
#                 field.widget.attrs.update({
#                     'class': 'form-control'
#                 })
#             elif isinstance(field.widget, forms.CheckboxInput):
#                 field.widget.attrs.update({
#                     'class': 'form-check-input'
#                 })

# class EmployeeFilterForm(BaseFilterForm):
#     """Form for filtering Employee records"""
    
#     department = forms.ModelChoiceField(
#         queryset=Department.objects.all(),
#         required=False,
#         empty_label="All Departments",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
    
#     designation = forms.ModelChoiceField(
#         queryset=Designation.objects.all(),
#         required=False,
#         empty_label="All Designations",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
    
#     is_active = forms.ChoiceField(
#         choices=[('', 'All Status'), ('true', 'Active'), ('false', 'Inactive')],
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )

from django import forms
from ..models import Employee, Department, Designation, Shift
from config.forms import CustomTextarea, BaseFilterForm
import random
import string
from django.db.models import Max
from decimal import Decimal

class EmployeeForm(forms.ModelForm):
    """Form for creating and updating Employee records"""

    # Personal Information fields
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="First Name"
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Last Name"
    )
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Full Name"
    )
    father_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Father's Name"
    )
    mother_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Mother's Name"
    )
    card_no = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Card Number"
    )
    gender = forms.ChoiceField(
        choices=Employee.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Gender"
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date of Birth"
    )
    blood_group = forms.ChoiceField(
        choices=Employee.BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Blood Group"
    )
    marital_status = forms.ChoiceField(
        choices=Employee.MARITAL_STATUS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Marital Status"
    )

    # Contact Information fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email"
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Phone"
    )
    emergency_contact_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Emergency Contact Name"
    )
    emergency_contact_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Emergency Contact Phone"
    )

    # Address Information fields
    present_address = forms.CharField(
        required=True,
        widget=CustomTextarea(attrs={'class': 'form-control'}),
        label="Present Address"
    )
    permanent_address = forms.CharField(
        required=False,
        widget=CustomTextarea(attrs={'class': 'form-control'}),
        label="Permanent Address"
    )

    # Employment Information fields
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Department"
    )
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Designation"
    )
    default_shift = forms.ModelChoiceField(
        queryset=Shift.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Default Shift"
    )
    joining_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Joining Date"
    )
    confirmation_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Confirmation Date"
    )
    expected_work_hours = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Expected Work Hours"
    )
    overtime_grace_minutes = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Overtime Grace Minutes"
    )

    # Salary Information fields
    basic_salary = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Basic Salary"
    )
    gross_salary = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label="Gross Salary"
    )

    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name',
            'card_no', 'gender', 'date_of_birth', 'blood_group', 'marital_status',
            'email', 'phone', 'emergency_contact_name', 'emergency_contact_phone',
            'present_address', 'permanent_address', 'department', 'designation',
            'default_shift', 'joining_date', 'confirmation_date', 'basic_salary',
            'gross_salary', 'is_active', 'profile_picture', 'expected_work_hours',
            'overtime_grace_minutes'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    fieldsets = [
        {
            'title': 'Personal Information',
            'description': 'Enter the personal details of the employee',
            'icon': 'user',
            'fields': [
                'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name',
                'card_no', 'gender', 'date_of_birth', 'blood_group', 'marital_status'
            ],
        },
        {
            'title': 'Contact Information',
            'description': 'Contact details for communication',
            'icon': 'phone',
            'fields': ['email', 'phone', 'emergency_contact_name', 'emergency_contact_phone'],
        },
        {
            'title': 'Address Information',
            'description': 'Employee address details',
            'icon': 'home',
            'fields': ['present_address', 'permanent_address'],
        },
        {
            'title': 'Employment Information',
            'description': 'Details of employment and role',
            'icon': 'briefcase',
            'fields': [
                'department', 'designation', 'default_shift', 'joining_date',
                'confirmation_date', 'expected_work_hours', 'overtime_grace_minutes'
            ],
        },
        {
            'title': 'Salary Information',
            'description': 'Salary details for the employee',
            'icon': 'dollar-sign',
            'fields': ['basic_salary', 'gross_salary', 'is_active'],
        },
        {
            'title': 'Profile Picture',
            'description': 'Upload employee profile picture',
            'icon': 'image',
            'fields': ['profile_picture'],
        },
    ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Auto-generate unique employee_id for new instances
        if not instance:
            self.initial['employee_id'] = self.generate_unique_code()

        # Apply styling to fields (already partially handled in field definitions)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control', 'type': 'date'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, CustomTextarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

        # Populate fields from instance if available
        if instance:
            # Personal Information
            self.initial['first_name'] = instance.first_name
            self.initial['last_name'] = instance.last_name
            self.initial['name'] = instance.name
            self.initial['father_name'] = instance.father_name
            self.initial['mother_name'] = instance.mother_name
            self.initial['card_no'] = instance.card_no
            self.initial['gender'] = instance.gender
            self.initial['date_of_birth'] = instance.date_of_birth
            self.initial['blood_group'] = instance.blood_group
            self.initial['marital_status'] = instance.marital_status

            # Contact Information
            self.initial['email'] = instance.email
            self.initial['phone'] = instance.phone
            self.initial['emergency_contact_name'] = instance.emergency_contact_name
            self.initial['emergency_contact_phone'] = instance.emergency_contact_phone

            # Address Information
            self.initial['present_address'] = instance.present_address
            self.initial['permanent_address'] = instance.permanent_address

            # Employment Information
            self.initial['department'] = instance.department
            self.initial['designation'] = instance.designation
            self.initial['default_shift'] = instance.default_shift
            self.initial['joining_date'] = instance.joining_date
            self.initial['confirmation_date'] = instance.confirmation_date
            self.initial['expected_work_hours'] = instance.expected_work_hours
            self.initial['overtime_grace_minutes'] = instance.overtime_grace_minutes

            # Salary Information
            self.initial['basic_salary'] = instance.basic_salary
            self.initial['gross_salary'] = instance.gross_salary
            self.initial['is_active'] = instance.is_active
            self.initial['profile_picture'] = instance.profile_picture

    def generate_unique_code(self):
        """Generate a unique employee_id for a new employee"""
        prefix = "EMP"
        try:
            # Find the highest numeric code
            last_employee = Employee.objects.filter(
                employee_id__startswith=prefix
            ).aggregate(
                Max('employee_id')
            )['employee_id__max']

            if last_employee:
                # Extract the numeric part
                try:
                    last_num = int(last_employee[len(prefix):])
                    new_num = last_num + 1
                    return f"{prefix}{new_num:04d}"
                except ValueError:
                    pass
        except Exception:
            pass

        # Fallback: Generate a random code
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{random_part}"

    def save(self, commit=True):
        """Save the employee instance with all fields"""
        employee = super().save(commit=commit)

        if commit:
            # Ensure gross_salary is not None
            if employee.gross_salary is None:
                employee.gross_salary = Decimal('0.00')
            employee.save()

        return employee

class EmployeeFilterForm(BaseFilterForm):
    """Form for filtering Employee records"""
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        empty_label="All Designations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'All Status'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )