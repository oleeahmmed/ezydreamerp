from django import forms
from datetime import datetime, timedelta

from ..models import (
    SalaryComponent, EmployeeSalaryStructure, SalaryStructureComponent,
    BonusSetup, BonusMonth, EmployeeBonus, AdvanceSetup, EmployeeAdvance,
    AdvanceInstallment, SalaryMonth, EmployeeSalary, SalaryDetail,
    Promotion, Increment, Deduction, Employee, Designation
)
from config.forms import CustomTextarea, BaseFilterForm

class SalaryComponentForm(forms.ModelForm):
    """Form for creating and updating Salary Component records"""
    
    class Meta:
        model = SalaryComponent
        fields = ['name', 'code', 'component_type', 'is_taxable', 'is_fixed', 'description']
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
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })

class EmployeeSalaryStructureForm(forms.ModelForm):
    """Form for creating and updating Employee Salary Structure records"""
    
    class Meta:
        model = EmployeeSalaryStructure
        fields = ['employee', 'effective_date', 'gross_salary']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class SalaryStructureComponentForm(forms.ModelForm):
    """Form for creating and updating Salary Structure Component records"""
    
    class Meta:
        model = SalaryStructureComponent
        fields = ['salary_structure', 'component', 'amount', 'percentage']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class BonusSetupForm(forms.ModelForm):
    """Form for creating and updating Bonus Setup records"""
    
    class Meta:
        model = BonusSetup
        fields = ['name', 'description']
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

class BonusMonthForm(forms.ModelForm):
    """Form for creating and updating Bonus Month records"""
    
    class Meta:
        model = BonusMonth
        fields = ['bonus_setup', 'year', 'month', 'is_generated']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
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
        
        # Add month choices
        self.fields['month'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['month'].choices = [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ]

class EmployeeBonusForm(forms.ModelForm):
    """Form for creating and updating Employee Bonus records"""
    
    class Meta:
        model = EmployeeBonus
        fields = ['bonus_month', 'employee', 'amount', 'remarks']
        widgets = {
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class AdvanceSetupForm(forms.ModelForm):
    """Form for creating and updating Advance Setup records"""
    
    class Meta:
        model = AdvanceSetup
        fields = ['name', 'max_amount', 'max_installments', 'interest_rate', 'description']
        widgets = {
            'description': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class EmployeeAdvanceForm(forms.ModelForm):
    """Form for creating and updating Employee Advance records"""
    
    class Meta:
        model = EmployeeAdvance
        fields = [
            'employee', 'advance_setup', 'amount', 'installments', 'installment_amount',
            'interest_amount', 'total_amount', 'application_date', 'status', 'reason', 'remarks'
        ]
        widgets = {
            'application_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': CustomTextarea(),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class AdvanceInstallmentForm(forms.ModelForm):
    """Form for creating and updating Advance Installment records"""
    
    class Meta:
        model = AdvanceInstallment
        fields = ['advance', 'installment_number', 'amount', 'due_date', 'is_paid', 'payment_date', 'remarks']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
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

class SalaryMonthForm(forms.ModelForm):
    """Form for creating and updating Salary Month records"""
    
    class Meta:
        model = SalaryMonth
        fields = ['year', 'month', 'is_generated', 'is_paid', 'payment_date', 'remarks']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': CustomTextarea(),
        }
    
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

class EmployeeSalaryForm(forms.ModelForm):
    """Form for creating and updating Employee Salary records"""
    
    class Meta:
        model = EmployeeSalary
        fields = [
            'salary_month', 'employee', 'basic_salary', 'gross_salary',
            'total_earnings', 'total_deductions', 'net_salary', 'working_days',
            'present_days', 'absent_days', 'leave_days', 'overtime_hours',
            'overtime_amount', 'is_separation_salary', 'remarks'
        ]
        widgets = {
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
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

class SalaryDetailForm(forms.ModelForm):
    """Form for creating and updating Salary Detail records"""
    
    class Meta:
        model = SalaryDetail
        fields = ['salary', 'component', 'amount']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class PromotionForm(forms.ModelForm):
    """Form for creating and updating Promotion records"""
    
    class Meta:
        model = Promotion
        fields = [
            'employee', 'from_designation', 'to_designation',
            'effective_date', 'salary_increment', 'remarks'
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)
        
        # Set from_designation to employee's current designation
        if 'employee' in self.data:
            try:
                employee_id = int(self.data.get('employee'))
                employee = Employee.objects.get(id=employee_id)
                self.fields['from_designation'].initial = employee.designation
            except (ValueError, Employee.DoesNotExist):
                pass

class IncrementForm(forms.ModelForm):
    """Form for creating and updating Increment records"""
    
    class Meta:
        model = Increment
        fields = ['employee', 'amount', 'percentage', 'effective_date', 'remarks']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class DeductionForm(forms.ModelForm):
    """Form for creating and updating Deduction records"""
    
    class Meta:
        model = Deduction
        fields = ['employee', 'salary_month', 'amount', 'reason']
        widgets = {
            'reason': CustomTextarea(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.NumberInput, forms.TextInput)):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Only show active employees
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True)

class PayrollFilterForm(BaseFilterForm):
    """Form for filtering Payroll records"""
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        required=False,
        choices=[('', 'All Years')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    month = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Months'),
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add year choices (current year and 5 years back)
        current_year = datetime.now().year
        year_choices = [('', 'All Years')]
        for year in range(current_year, current_year - 6, -1):
            year_choices.append((year, str(year)))
        self.fields['year'].choices = year_choices