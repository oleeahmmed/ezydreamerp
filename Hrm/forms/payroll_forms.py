from django import forms
from datetime import datetime, timedelta
from django.forms import inlineformset_factory
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
        fields = ['employee', 'effective_date', 'basic_salary']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'basic_salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': '0'}),
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
        
        # Add labels for better UX
        self.fields['employee'].label = "Employee"
        self.fields['effective_date'].label = "Effective Date"
        self.fields['basic_salary'].label = "Basic Salary"
        
        # Add help text
        self.fields['basic_salary'].help_text = "Base salary amount (earnings and deductions will be calculated automatically)"
        
        # If updating, show calculated values as read-only
        if self.instance and self.instance.pk:
            self.fields['gross_salary_display'] = forms.CharField(
                label="Gross Salary",
                initial=f"{self.instance.gross_salary:,.2f}",
                widget=forms.TextInput(attrs={'readonly': True, 'class': 'form-control bg-light'}),
                required=False,
                help_text="Automatically calculated from basic salary + earnings"
            )
            self.fields['net_salary_display'] = forms.CharField(
                label="Net Salary",
                initial=f"{self.instance.net_salary:,.2f}",
                widget=forms.TextInput(attrs={'readonly': True, 'class': 'form-control bg-light'}),
                required=False,
                help_text="Automatically calculated as gross salary - deductions"
            )

    def clean_basic_salary(self):
        basic_salary = self.cleaned_data.get('basic_salary')
        if basic_salary and basic_salary < 0:
            raise forms.ValidationError("Basic salary cannot be negative.")
        return basic_salary

class SalaryStructureComponentForm(forms.ModelForm):
    """Form for creating and updating Salary Structure Component records"""
    
    calculation_type = forms.ChoiceField(
        choices=[('amount', 'Fixed Amount'), ('percentage', 'Percentage')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='amount',
        help_text="Choose how to calculate this component"
    )
    
    class Meta:
        model = SalaryStructureComponent
        fields = ['salary_structure', 'component', 'amount', 'percentage', 'is_active']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': '0'}),
            'percentage': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'min': '0', 'max': '100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        
        # Ensure component field has proper queryset
        self.fields['component'].queryset = SalaryComponent.objects.all().order_by('component_type', 'name')
        self.fields['component'].empty_label = "Select Component"
        
        # Add labels
        self.fields['component'].label = "Salary Component"
        self.fields['amount'].label = "Fixed Amount"
        self.fields['percentage'].label = "Percentage (%)"
        self.fields['is_active'].label = "Active"
        
        # Add help text
        self.fields['amount'].help_text = "Fixed amount for this component"
        self.fields['percentage'].help_text = "Percentage of basic salary (for earnings) or gross salary (for deductions)"
        
        # Set initial calculation type based on existing data
        if self.instance and self.instance.pk:
            if self.instance.percentage:
                self.fields['calculation_type'].initial = 'percentage'
            else:
                self.fields['calculation_type'].initial = 'amount'
        
        # If this is an existing instance, show calculated amount
        if self.instance and self.instance.pk:
            self.fields['calculated_amount_display'] = forms.CharField(
                label="Calculated Amount",
                initial=f"{self.instance.calculated_amount:,.2f}",
                widget=forms.TextInput(attrs={'readonly': True, 'class': 'form-control bg-light'}),
                required=False,
                help_text="Final calculated amount for this component"
            )

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        percentage = cleaned_data.get('percentage')
        calculation_type = cleaned_data.get('calculation_type')
        
        # Clear the field that's not being used
        if calculation_type == 'amount':
            cleaned_data['percentage'] = None
            if not amount:
                raise forms.ValidationError("Amount is required when using fixed amount calculation.")
        elif calculation_type == 'percentage':
            cleaned_data['amount'] = None
            if not percentage:
                raise forms.ValidationError("Percentage is required when using percentage calculation.")
        
        # Validate values
        if amount and amount < 0:
            raise forms.ValidationError("Amount cannot be negative.")
        
        if percentage and (percentage < 0 or percentage > 100):
            raise forms.ValidationError("Percentage must be between 0 and 100.")
        
        return cleaned_data

# Create formset for SalaryStructureComponent
SalaryStructureComponentFormSet = inlineformset_factory(
    EmployeeSalaryStructure,
    SalaryStructureComponent,
    form=SalaryStructureComponentForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

class EmployeeSalaryStructureFilterForm(BaseFilterForm):
    """Form for filtering Employee Salary Structure records"""
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    effective_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Effective Date From"
    )
    
    effective_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Effective Date To"
    )
    
    min_salary = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        label="Minimum Salary"
    )
    
    max_salary = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        label="Maximum Salary"
    )


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