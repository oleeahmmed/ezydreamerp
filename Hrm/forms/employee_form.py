from django import forms
from ..models import Employee, Department, Designation, Shift, Document # Assuming Document model exists
from config.forms import CustomTextarea, BaseFilterForm
import random
import string
from django.db.models import Max
from decimal import Decimal
from django.forms import ModelForm

class EmployeeForm(ModelForm):
    """Form for creating and updating Employee records"""
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name', 'card_no', 
            'gender', 'date_of_birth', 'nid_no', 'religion', 'blood_group', 'default_shift', 'marital_status', 
            'mailing_care_of', 'mailing_village_town', 'mailing_district', 'mailing_upazila_thana', 'mailing_union', 
            'mailing_post_office', 'mailing_post_code', 'mailing_home_phone', 'mailing_mobile', 'mailing_email', 
            'permanent_care_of', 'permanent_village_town', 'permanent_district', 'permanent_upazila_thana', 
            'permanent_union', 'permanent_post_office', 'permanent_post_code', 'permanent_home_phone', 
            'permanent_mobile', 'permanent_email', 'education_qualification', 'major_subject', 'institution', 
            'university_board', 'passing_year', 'result', 'department', 'designation', 'joining_date', 
            'expected_work_hours', 'overtime_grace_minutes', 'basic_salary', 'gross_salary', 'profile_picture', 
            'is_active', 'documents'
        ]
    
    widgets = {
        'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        # If you had DateTimeField or TimeField, you'd add them here with 'datetime-local' or 'time'
        # 'some_datetime_field': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        # 'some_time_field': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'education_qualification': forms.Select(attrs={'class': 'form-control'}),
        'department': forms.Select(attrs={'class': 'form-control'}),
        'designation': forms.Select(attrs={'class': 'form-control'}),
        'default_shift': forms.Select(attrs={'class': 'form-control'}),
        'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'mailing_care_of': CustomTextarea(attrs={'class': 'form-control'}),
        'mailing_village_town': CustomTextarea(attrs={'class': 'form-control'}),
        'permanent_care_of': CustomTextarea(attrs={'class': 'form-control'}),
        'permanent_village_town': CustomTextarea(attrs={'class': 'form-control'}),
    }

    # Define fieldsets for organizing fields into collapsible sections
    fieldsets = [
        {
            'id': 'personal-info', # Unique ID for the collapse section
            'title': 'Personal Information',
            'description': 'Enter the personal details of the employee',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': [
                'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name', 'card_no', 
                'gender', 'date_of_birth', 'nid_no', 'religion', 'blood_group', 'marital_status'
            ],
            'collapsed': False, # Default state: expanded
        },
        {
            'id': 'contact-info',
            'title': 'Contact Information',
            'description': 'Employee contact details (Mailing and Permanent)',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': [
                'mailing_care_of', 'mailing_village_town', 'mailing_district', 'mailing_upazila_thana', 'mailing_union', 
                'mailing_post_office', 'mailing_post_code', 'mailing_home_phone', 'mailing_mobile', 'mailing_email', 
                'permanent_care_of', 'permanent_village_town', 'permanent_district', 'permanent_upazila_thana', 
                'permanent_union', 'permanent_post_office', 'permanent_post_code', 'permanent_home_phone', 
                'permanent_mobile', 'permanent_email'
            ],
            'collapsed': True, # Default state: collapsed
        },
        {
            'id': 'educational-info',
            'title': 'Educational Information',
            'description': 'Information about employee’s education qualifications',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21.43 10.99l-9.14 5.26a2 2 0 0 1-2.18 0L2.57 10.99a2 2 0 0 1 0-3.46l9.14-5.26a2 2 0 0 1 2.18 0l9.14 5.26a2 2 0 0 1 0 3.46z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M7.5 4.21L12 6.84L16.5 4.21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 17.5V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 11.5L12 17L21.5 11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': [
                'education_qualification', 'major_subject', 'institution', 'university_board', 'passing_year', 'result'
            ],
            'collapsed': True,
        },
        {
            'id': 'employment-info',
            'title': 'Employment Information',
            'description': 'Employee’s department, designation, and work-related details',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="7" width="20" height="14" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': [
                'department', 'designation', 'default_shift', 'joining_date', 'expected_work_hours', 'overtime_grace_minutes'
            ],
            'collapsed': True,
        },
        {
            'id': 'salary-info',
            'title': 'Salary Information',
            'description': 'Salary details for the employee',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': [
                'basic_salary', 'gross_salary'
            ],
            'collapsed': True,
        },
        {
            'id': 'profile-docs',
            'title': 'Profile & Documents',
            'description': 'Upload employee profile picture and other documents',
            'icon': '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="9" r="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            'fields': ['profile_picture', 'documents', 'is_active'],
            'collapsed': True,
        },
    ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Auto-generate unique employee_id for new instances
        if not instance:
            self.initial['employee_id'] = self.generate_unique_code()

        # Apply styling to fields
        for field_name, field in self.fields.items():
            # Ensure all text-based inputs get the form-control class
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, 
                                         forms.DateInput, forms.TimeInput, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, CustomTextarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

        # Populate fields from instance if available (handled by ModelForm, but keeping for reference)
        if instance:
            # This block is largely redundant for a ModelForm as it automatically populates
            # initial data from the instance. It's kept here for consistency with your
            # previous snippets, but can typically be removed for cleaner code.
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
            self.initial['nid_no'] = instance.nid_no
            self.initial['religion'] = instance.religion

            self.initial['mailing_care_of'] = instance.mailing_care_of
            self.initial['mailing_village_town'] = instance.mailing_village_town
            self.initial['mailing_district'] = instance.mailing_district
            self.initial['mailing_upazila_thana'] = instance.mailing_upazila_thana
            self.initial['mailing_union'] = instance.mailing_union
            self.initial['mailing_post_office'] = instance.mailing_post_office
            self.initial['mailing_post_code'] = instance.mailing_post_code
            self.initial['mailing_home_phone'] = instance.mailing_home_phone
            self.initial['mailing_mobile'] = instance.mailing_mobile
            self.initial['mailing_email'] = instance.mailing_email

            self.initial['permanent_care_of'] = instance.permanent_care_of
            self.initial['permanent_village_town'] = instance.permanent_village_town
            self.initial['permanent_district'] = instance.permanent_district
            self.initial['permanent_upazila_thana'] = instance.permanent_upazila_thana
            self.initial['permanent_union'] = instance.permanent_union
            self.initial['permanent_post_office'] = instance.permanent_post_office
            self.initial['permanent_post_code'] = instance.permanent_post_code
            self.initial['permanent_home_phone'] = instance.permanent_home_phone
            self.initial['permanent_mobile'] = instance.permanent_mobile
            self.initial['permanent_email'] = instance.permanent_email

            self.initial['education_qualification'] = instance.education_qualification
            self.initial['major_subject'] = instance.major_subject
            self.initial['institution'] = instance.institution
            self.initial['university_board'] = instance.university_board
            self.initial['passing_year'] = instance.passing_year
            self.initial['result'] = instance.result

            self.initial['department'] = instance.department
            self.initial['designation'] = instance.designation
            self.initial['default_shift'] = instance.default_shift
            self.initial['joining_date'] = instance.joining_date
            self.initial['expected_work_hours'] = instance.expected_work_hours
            self.initial['overtime_grace_minutes'] = instance.overtime_grace_minutes

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


# from django import forms
# from ..models import Employee, Department, Designation, Shift
# from config.forms import CustomTextarea, BaseFilterForm
# import random
# import string
# from django.db.models import Max
# from decimal import Decimal
# from django.forms import ModelForm

# class EmployeeForm(ModelForm):
#     """Form for creating and updating Employee records"""
    
#     class Meta:
#         model = Employee
#         fields = [
#             'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name', 'card_no', 
#             'gender', 'date_of_birth', 'nid_no', 'religion', 'blood_group', 'default_shift', 'marital_status', 
#             'mailing_care_of', 'mailing_village_town', 'mailing_district', 'mailing_upazila_thana', 'mailing_union', 
#             'mailing_post_office', 'mailing_post_code', 'mailing_home_phone', 'mailing_mobile', 'mailing_email', 
#             'permanent_care_of', 'permanent_village_town', 'permanent_district', 'permanent_upazila_thana', 
#             'permanent_union', 'permanent_post_office', 'permanent_post_code', 'permanent_home_phone', 
#             'permanent_mobile', 'permanent_email', 'education_qualification', 'major_subject', 'institution', 
#             'university_board', 'passing_year', 'result', 'department', 'designation', 'joining_date', 
#             'expected_work_hours', 'overtime_grace_minutes', 'basic_salary', 'gross_salary', 'profile_picture', 
#             'is_active', 'documents'
#         ]
    
#     # Add widgets for specific field types to ensure correct HTML input types
#     widgets = {
#         'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         # Example for a DateTimeField if you had one in your model:
#         # 'some_datetime_field': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#         # Example for a TimeField if you had one in your model:
#         # 'some_time_field': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
#         'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
#         'education_qualification': forms.Select(attrs={'class': 'form-control'}),
#         'department': forms.Select(attrs={'class': 'form-control'}),
#         'designation': forms.Select(attrs={'class': 'form-control'}),
#         'default_shift': forms.Select(attrs={'class': 'form-control'}),
#         'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         'mailing_care_of': CustomTextarea(), # Using CustomTextarea for address fields
#         'mailing_village_town': CustomTextarea(),
#         'permanent_care_of': CustomTextarea(),
#         'permanent_village_town': CustomTextarea(),
#     }

#     # Organizing the fields into tabs (you can render these tabs in your templates)
#     fieldsets = [
#         {
#             'title': 'Personal Information',
#             'description': 'Enter the personal details of the employee',
#             'icon': 'user',
#             'fields': [
#                 'employee_id', 'first_name', 'last_name', 'name', 'father_name', 'mother_name', 'card_no', 
#                 'gender', 'date_of_birth', 'nid_no', 'religion', 'blood_group', 'marital_status'
#             ],
#         },
#         {
#             'title': 'Contact Information',
#             'description': 'Employee contact details (Mailing and Permanent)',
#             'icon': 'phone',
#             'fields': [
#                 'mailing_care_of', 'mailing_village_town', 'mailing_district', 'mailing_upazila_thana', 'mailing_union', 
#                 'mailing_post_office', 'mailing_post_code', 'mailing_home_phone', 'mailing_mobile', 'mailing_email', 
#                 'permanent_care_of', 'permanent_village_town', 'permanent_district', 'permanent_upazila_thana', 
#                 'permanent_union', 'permanent_post_office', 'permanent_post_code', 'permanent_home_phone', 
#                 'permanent_mobile', 'permanent_email'
#             ],
#         },
#         {
#             'title': 'Educational Information',
#             'description': 'Information about employee’s education qualifications',
#             'icon': 'graduation-cap',
#             'fields': [
#                 'education_qualification', 'major_subject', 'institution', 'university_board', 'passing_year', 'result'
#             ],
#         },
#         {
#             'title': 'Employment Information',
#             'description': 'Employee’s department, designation, and work-related details',
#             'icon': 'briefcase',
#             'fields': [
#                 'department', 'designation', 'default_shift', 'joining_date', 'expected_work_hours', 'overtime_grace_minutes'
#             ],
#         },
#         {
#             'title': 'Salary Information',
#             'description': 'Salary details for the employee',
#             'icon': 'dollar-sign',
#             'fields': [
#                 'basic_salary', 'gross_salary'
#             ],
#         },
#         {
#             'title': 'Profile & Documents',
#             'description': 'Upload employee profile picture and other documents',
#             'icon': 'image',
#             'fields': ['profile_picture', 'documents', 'is_active'], # Added is_active to a fieldset
#         },
#     ]

#     def __init__(self, *args, **kwargs):
#         instance = kwargs.get('instance', None)
#         super().__init__(*args, **kwargs)

#         # Auto-generate unique employee_id for new instances
#         if not instance:
#             self.initial['employee_id'] = self.generate_unique_code()

#         # Apply styling to fields (already partially handled in field definitions)
#         for field_name, field in self.fields.items():
#             # Ensure all text-based inputs get the form-control class
#             if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, 
#                                          forms.DateInput, forms.TimeInput, forms.DateTimeInput)):
#                 field.widget.attrs.update({'class': 'form-control'})
#             elif isinstance(field.widget, forms.Select):
#                 field.widget.attrs.update({'class': 'form-control'})
#             elif isinstance(field.widget, forms.CheckboxInput):
#                 field.widget.attrs.update({'class': 'form-check-input'})
#             elif isinstance(field.widget, CustomTextarea):
#                 field.widget.attrs.update({'class': 'form-control'})
#             elif isinstance(field.widget, forms.FileInput):
#                 field.widget.attrs.update({'class': 'form-control'})

#         # Populate fields from instance if available (this is usually handled by ModelForm automatically,
#         # but explicit initial values can be useful for debugging or specific overrides)
#         # However, for a ModelForm, it's generally better to let the form handle initial data
#         # based on the `instance` passed to it, rather than manually setting `self.initial`.
#         # The code below is kept for reference as it was in your original snippet, but
#         # for a standard ModelForm usage, it might be redundant.
#         if instance:
#             self.initial['first_name'] = instance.first_name
#             self.initial['last_name'] = instance.last_name
#             self.initial['name'] = instance.name
#             self.initial['father_name'] = instance.father_name
#             self.initial['mother_name'] = instance.mother_name
#             self.initial['card_no'] = instance.card_no
#             self.initial['gender'] = instance.gender
#             self.initial['date_of_birth'] = instance.date_of_birth
#             self.initial['blood_group'] = instance.blood_group
#             self.initial['marital_status'] = instance.marital_status
#             self.initial['nid_no'] = instance.nid_no
#             self.initial['religion'] = instance.religion

#             self.initial['mailing_care_of'] = instance.mailing_care_of
#             self.initial['mailing_village_town'] = instance.mailing_village_town
#             self.initial['mailing_district'] = instance.mailing_district
#             self.initial['mailing_upazila_thana'] = instance.mailing_upazila_thana
#             self.initial['mailing_union'] = instance.mailing_union
#             self.initial['mailing_post_office'] = instance.mailing_post_office
#             self.initial['mailing_post_code'] = instance.mailing_post_code
#             self.initial['mailing_home_phone'] = instance.mailing_home_phone
#             self.initial['mailing_mobile'] = instance.mailing_mobile
#             self.initial['mailing_email'] = instance.mailing_email

#             self.initial['permanent_care_of'] = instance.permanent_care_of
#             self.initial['permanent_village_town'] = instance.permanent_village_town
#             self.initial['permanent_district'] = instance.permanent_district
#             self.initial['permanent_upazila_thana'] = instance.permanent_upazila_thana
#             self.initial['permanent_union'] = instance.permanent_union
#             self.initial['permanent_post_office'] = instance.permanent_post_office
#             self.initial['permanent_post_code'] = instance.permanent_post_code
#             self.initial['permanent_home_phone'] = instance.permanent_home_phone
#             self.initial['permanent_mobile'] = instance.permanent_mobile
#             self.initial['permanent_email'] = instance.permanent_email

#             self.initial['education_qualification'] = instance.education_qualification
#             self.initial['major_subject'] = instance.major_subject
#             self.initial['institution'] = instance.institution
#             self.initial['university_board'] = instance.university_board
#             self.initial['passing_year'] = instance.passing_year
#             self.initial['result'] = instance.result

#             self.initial['department'] = instance.department
#             self.initial['designation'] = instance.designation
#             self.initial['default_shift'] = instance.default_shift
#             self.initial['joining_date'] = instance.joining_date
#             self.initial['expected_work_hours'] = instance.expected_work_hours
#             self.initial['overtime_grace_minutes'] = instance.overtime_grace_minutes

#             self.initial['basic_salary'] = instance.basic_salary
#             self.initial['gross_salary'] = instance.gross_salary
#             self.initial['is_active'] = instance.is_active
#             self.initial['profile_picture'] = instance.profile_picture


#     def generate_unique_code(self):
#         """Generate a unique employee_id for a new employee"""
#         prefix = "EMP"
#         try:
#             # Find the highest numeric code
#             last_employee = Employee.objects.filter(
#                 employee_id__startswith=prefix
#             ).aggregate(
#                 Max('employee_id')
#             )['employee_id__max']

#             if last_employee:
#                 # Extract the numeric part
#                 try:
#                     last_num = int(last_employee[len(prefix):])
#                     new_num = last_num + 1
#                     return f"{prefix}{new_num:04d}"
#                 except ValueError:
#                     pass
#         except Exception:
#             pass

#         # Fallback: Generate a random code
#         random_part = ''.join(random.choices(string.digits, k=4))
#         return f"{prefix}{random_part}"

#     def save(self, commit=True):
#         """Save the employee instance with all fields"""
#         employee = super().save(commit=commit)

#         if commit:
#             # Ensure gross_salary is not None
#             if employee.gross_salary is None:
#                 employee.gross_salary = Decimal('0.00')
#             employee.save()

#         return employee

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